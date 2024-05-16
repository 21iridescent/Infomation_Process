import streamlit as st
import pandas as pd
from openai import OpenAI
import openpyxl
import os

# 设置页面
st.set_page_config(page_title="法律文书批量处理助手", page_icon=":rocket:")

# 设置标题
st.title("法律文书批量处理助手")

# API key 输入框
api_key = st.text_input("输入API Key")

# 设置可用模型列表
available_models = [
    "mistralai/mistral-7b-instruct:free",
    "anthropic/claude-3-haiku:beta",
    "anthropic/claude-3-sonnet:beta",
    "meta-llama/llama-3-70b-instruct",
    "openai/gpt-4-turbo",
    "openai/gpt-4o",
    "anthropic/claude-3-opus:beta"
]

# 在页面顶部添加模型选择框
st.info("先用Free的模型测试一下，再选择GPT4或者其他贵的模型！模型价格和能力由低到高，建议按顺序先试试。")

model = st.selectbox("选择模型", available_models)

# 上传Excel文件
uploaded_file = st.file_uploader("上传Excel文件", type=["xlsx", "csv"])

# 如果文件已上传，让用户选择要处理的列
if uploaded_file:
    # 获取文件名
    uploaded_file_name = uploaded_file.name

    # 读取Excel文件或者CSV文件
    if uploaded_file_name.endswith('.xlsx'):
        df = pd.read_excel(uploaded_file)
    elif uploaded_file_name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)

    column_to_process = st.selectbox("选择要处理的列", df.columns)

    # Prompt模板列表
    prompt_templates = {
        "翻译": "作为专业的语言翻译家，请将以下新闻内容翻译成英文。",
        "关键词": "作为经验丰富的法律顾问，请从以下文本中提取关键的法律术语。",
        "总结": "请对以下新闻内容进行总结，并提炼出最重要的主要内容。生成一句话中文总结。10-20字左右"
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

        # Initialize download button placeholder
        download_button_placeholder = st.empty()

        # If num_rows is specified, only process that many rows
        if num_rows is not None:
            df = df.head(num_rows)

        total_rows = len(df)
        results = []
        processed_data = []

        for index, row in df.iterrows():
            combined_prompt = f"##{user_prompt}\n\n ## 待处理的文本: {row[column_to_process]}"
            print(combined_prompt)
            try:
                completion = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": combined_prompt}],
                )
                results.append(completion.choices[0].message.content)
                processed_data.append((index, completion.choices[0].message.content))
                st.write(f"Row {index + 1} result: {completion.choices[0].message.content}")
            except Exception as e:
                st.error(f"API request failed on row {index + 1}: {e}")
                results.append("Error: Unable to process this row.")
                continue

            # Update the progress bar
            progress = int((index + 1) / total_rows * 100)
            progress_bar.progress(progress)

            # Delete the old xlxs file
            if index > 0:
                file_name = f"processed_output_{index}.xlsx"
                try:
                    os.remove(file_name)
                except Exception as e:
                    pass

            # Check to generate download link every ten rows or at the end of the DataFrame
            if (index + 1) % 1 == 0 or (index + 1) == total_rows:
                file_name = f"{uploaded_file_name}_处理到第{index + 1}行.xlsx"

                # Slice the df to the current index
                df_slice = df.iloc[:index + 1]
                # Append the results to the df_slice with .loc[row_indexer,col_indexer] = value
                df_slice.loc[:, '大模型处理结果'] = results

                with pd.ExcelWriter(file_name) as writer:
                    df_slice.to_excel(writer, index=False)

                # Update the download button in the placeholder
                with open(file_name, "rb") as file:
                    download_button_placeholder.download_button(f"Download processed data up to row {index + 1}", file,
                                                                file_name=file_name, mime="application/vnd.ms-excel")

        df['大模型处理结果'] = results

        return df

    # 处理1行按钮
    if st.button("处理1行试试"):
        if user_prompt:
            # 处理1行作为测试
            results = process_data(df, column_to_process, user_prompt, num_rows=1)
            st.write(results)
        else:
            st.error("请输入提示内容。")

    # 处理前3行按钮
    if st.button("处理前3行试试"):
        if user_prompt:
            # 处理前3行作为测试
            results = process_data(df, column_to_process, user_prompt, num_rows=3)
            st.write(results)
        else:
            st.error("请输入提示内容。")

    # 处理全部数据按钮
    if st.button("测试完了！全部处理（贵贵贵）！"):
        if user_prompt:
            try:
                processed_df = process_data(df, column_to_process, user_prompt)
                output_filename = uploaded_file_name.split('.')[0] + '_处理后.xlsx'
                processed_df.to_excel(output_filename, index=False)
            except Exception as e:
                st.error(f"Failed to save the processed data: {e}")
            else:
                st.success("处理完成！")
                with open(output_filename, "rb") as file:
                    st.download_button(label="下载处理后的Excel文件",
                                       data=file,
                                       file_name=output_filename,
                                       mime="application/vnd.ms-excel")
        else:
            st.error("请输入提示内容。")
else:
    st.error("请上传文件~")
