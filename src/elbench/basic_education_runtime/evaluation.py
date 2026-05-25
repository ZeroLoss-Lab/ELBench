import re
from typing import Any, Dict
from langchain_core.tools import tool, BaseTool
from elbench.basic_education_runtime.config import CONFIG
from langgraph.prebuilt import create_react_agent
from langchain.chat_models.base import BaseChatModel
from elbench.basic_education_runtime.entity import ExportFormat
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_fixed
import json


def generate_evaluation_tool() -> BaseTool:
    """
    Generates a tool for evaluating the basic education runtime outputs.
    This function is a placeholder and should be implemented with actual logic.
    """

    if CONFIG.evaluation is None:
        raise ValueError("Evaluation configuration not found.")

    @tool(
        name_or_callable="save_result_to_database",
        description="Save the evaluation results to a database.",
        return_direct=True,
        args_schema=CONFIG.evaluation.format_to_pydantic(),
    )
    def save_to_db(**kwargs):
        """
        Save the evaluation results to a database.
        """
        for k, v in kwargs.items():
            if issubclass(v.__class__, BaseModel):
                v = v.model_dump()
            kwargs[k] = v
        return kwargs

    return save_to_db


@retry(
    stop=stop_after_attempt(CONFIG.globals.retry.attempt),
    wait=wait_fixed(CONFIG.globals.retry.interval),
)
async def evaluate(
    model: BaseChatModel, exported_result: ExportFormat
) -> Dict[str, Any]:
    assert CONFIG.evaluation
    system_prompt, other_prompt = CONFIG.evaluation.get_prompts()
    system_prompt = exported_result.replace_template(system_prompt)
    ops = []
    for op in other_prompt:
        content = exported_result.replace_template(op.content)
        ops.append(
            {
                "role": op.role,
                "content": content,
            }
        )
    if CONFIG.evaluation.format_mode == "tool":
        tools = [generate_evaluation_tool()]

        # other_prompt = exported_result.replace_template(other_prompt)
        agent = create_react_agent(
            model=model.bind_tools(
                tools,
                tool_choice={
                    "type": "function",
                    "function": {"name": "save_result_to_database"},
                },  # type: ignore
                # tool_choice="required",
            ),
            tools=tools,
            # model=model,
            prompt=system_prompt
            + "\n\nPlease call the save_result_to_database tool to store the evaluation result.",
        )

        a = await agent.ainvoke({"messages": ops})
        data = json.loads(a["messages"][-1].content)
        return data
    elif CONFIG.evaluation.format_mode == "prompt":
        format_example = CONFIG.evaluation.format_to_json_example()
        agent = create_react_agent(
            model=model,
            tools=[],
            prompt=system_prompt
            + "\n\nReturn exactly one JSON object wrapped with <START OF EVAL OUTPUT> and <END OF EVAL OUTPUT>."
            + "\nDo not add markdown fences, explanations, or extra text."
            + "\nUse the same keys and value types as this example:\n"
            + "\n<START OF EVAL OUTPUT>\n"
            + f"{format_example}\n"
            + "<END OF EVAL OUTPUT>",
        )

        a = await agent.ainvoke({"messages": ops})
        response: str = a["messages"][-1].content

        # Fuck Gemini
        response = response.replace("\\<", "<")
        response = response.replace("\\>", ">")

        # print(response)

        # 姝ｅ垯琛ㄨ揪寮忓尮閰?START OUTPUT>鍜?END OUTPUT>
        match = re.findall(
            r"<START OF EVAL OUTPUT>(.*)<END OF EVAL OUTPUT>", response, re.DOTALL
        )
        if len(match) > 0:
            text = match[-1]
            # 濡傛灉text琚玚``鍖呭洿锛屽幓鎺?
            text = text.strip().strip("```").strip("json")
            # print(text, "#############")
            return json.loads(text)
        else:
            raise ValueError("Output does not contain <START OUTPUT> and <END OUTPUT>")
    else:
        raise ValueError(f"Invalid format mode: {CONFIG.evaluation.format_mode}")


if __name__ == "__main__":
    import asyncio

    async def main():
        from elbench.basic_education_runtime.model import init_chat_model_from_dict
        # from langchain.globals import set_debug

        # set_debug(True)

        ef = ExportFormat.from_json_file(
            "/tmp/basic_education_runtime/sample.json"
        )

        model = init_chat_model_from_dict(CONFIG.models["4o_teacher"])
        a = await evaluate(model, ef)
        print(a)

    asyncio.run(main())

