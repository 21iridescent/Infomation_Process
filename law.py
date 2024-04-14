import streamlit as st
import pandas as pd
from openai import OpenAI
import openpyxl

# 设置页面
st.set_page_config(page_title="法律文书批量处理助手", page_icon=":rocket:")

#设置标题
st.title("法律文书批量处理助手")

#api key输入框
api_key = st.text_input("输入API Key")

# 设置可用模型列表
available_models = [
    "mistralai/mistral-7b-instruct:free",
    "anthropic/claude-3-haiku:beta",
    "anthropic/claude-3-sonnet:beta",
    "openai/gpt-4-turbo",
    "anthropic/claude-3-opus:beta"
]


# 在页面顶部添加模型选择框
st.info("先用Free的模型测试一下，再选择GPT4或者其他贵的模型！模型价格you")

model = st.selectbox("选择模型", available_models)

# 上传Excel文件
uploaded_file = st.file_uploader("上传Excel文件", type=["xlsx"])

# 如果文件已上传，让用户选择要处理的列
if uploaded_file:
    # 读取Excel文件
    df = pd.read_excel(uploaded_file)
    column_to_process = st.selectbox("选择要处理的列", df.columns)

    # Prompt模板列表
    prompt_templates = {
        "翻译": "作为专业的语言翻译家，请将以下新闻内容翻译成英文。",
        "关键词": "作为经验丰富的法律顾问，请从以下文本中提取关键的法律术语。",
        "总结": "作为资深的新闻编辑，请对以下新闻内容进行总结，并提炼出主要观点。",
        # 根据需要添加更多模板
    }

    # 选择Prompt模板
    template_key = st.selectbox("选择Prompt模板", options=list(prompt_templates.keys()))

    # 输入Prompt内容，展示默认提示
    user_prompt = st.text_area("输入ChatGPT提示内容：", value=prompt_templates[template_key])


    # 定义一个函数来处理数据
    def process_data(df, column_to_process, user_prompt, num_rows=None):
        # Initialize OpenAI client
        try:
            client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=api_key,
            )
        except Exception as e:
            st.error(f"Failed to initialize OpenAI client: {e}")
            return

        # Set up progress bar
        progress_bar = st.progress(0)

        # If num_rows is specified, only process that many rows
        if num_rows is not None:
            df = df.head(num_rows)

        total_rows = len(df)
        results = []
        for index, row in df.iterrows():
            # Combine prompt and content from Excel "user_prompt" + "/t" + "#待处理的文本内容：" + {row[column_to_process]}
            combined_prompt = f"##{user_prompt}\n\n ##待处理的文本: {row[column_to_process]}"

            print(combined_prompt)
            try:
                completion = client.chat.completions.create(
                    model=model,
                    messages=[
                        {
                            "role": "user",
                            "content": combined_prompt,
                        },
                    ],
                )
                # Save model output
                results.append(completion.choices[0].message.content)
            except Exception as e:
                st.error(f"API request failed on row {index + 1}: {e}")
                results.append("Error: Unable to process this row.")
                continue

            # Only display the last 10 outputs --
            if total_rows - index <= 10:
                with st.expander(f"行 {index + 1} 的输出:"):
                    st.write(combined_prompt)
                    st.markdown("---")
                    # Check if 'completion' has 'choices' and if 'choices' is not empty
                    if completion.choices[0].message.content:
                        output_content = completion.choices[0].message.content
                    else:
                        output_content = "Error: No completion available or invalid response structure."

                    st.write(output_content)

            # Update the progress bar
            progress = int((index + 1) / total_rows * 100)
            progress_bar.progress(progress)

        # Append results to DataFrame
        df['大模型处理结果'] = results

        # Once completed, set progress bar to 100%
        progress_bar.progress(100)

        return df

    # 处理1行按钮
    if st.button("处理1行试试"):
        if user_prompt:
            # 处理1行作为测试
            process_data(df, column_to_process, user_prompt, num_rows=1)
        else:
            st.error("请输入提示内容。")

    # 处理前5行按钮
    if st.button("处理前3行试试"):
        if user_prompt:
            # 处理前5行作为测试
            process_data(df, column_to_process, user_prompt, num_rows=3)
        else:
            st.error("请输入提示内容。")

    # 处理全部数据按钮
    if st.button("测试完了！全部处理（贵贵贵）！"):
        if user_prompt:
            # Process all data
            try:
                processed_df = process_data(df, column_to_process, user_prompt)
                output_filename = 'processed_output.xlsx'
                processed_df.to_excel(output_filename, index=False)
            except Exception as e:
                st.error(f"Failed to save the processed data: {e}")
            else:
                # Provide a download link
                st.success("处理完成！")
                with open(output_filename, "rb") as file:
                    st.download_button(label="下载处理后的Excel文件",
                                       data=file,
                                       file_name=output_filename,
                                       mime="application/vnd.ms-excel")
        else:
            st.error("请输入提示内容。")
else:
    st.error("请上传文件。")