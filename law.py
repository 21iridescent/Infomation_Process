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
    "huggingfaceh4/zephyr-7b-beta:free",
    "anthropic/claude-3-haiku:beta",
    "openai/gpt-4-turbo",
    "anthropic/claude-3-sonnet:beta"
]


# 在页面顶部添加模型选择框
st.info("先用Free的模型测试一下，再选择GPT4或者其他贵的模型！！！")

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
        # 初始化OpenAI客户端
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )

        # 设置进度条
        progress_bar = st.progress(0)

        # 如果指定了num_rows，仅处理指定数量的行
        if num_rows is not None:
            df = df.head(num_rows)

        total_rows = len(df)
        results = []
        for index, row in df.iterrows():
            # 更新进度条
            progress = int((index + 1) / total_rows * 100)
            progress_bar.progress(progress)

            # 组合prompt和Excel中的内容 "user_prompt" + "/t" + "#待处理的文本内容：" + {row[column_to_process]}
            combined_prompt = f"##{user_prompt}\n\n ##待处理的文本: {row[column_to_process]}"

            print(combined_prompt)
            completion = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": combined_prompt,
                    },
                ],
            )
            # 保存模型输出
            results.append(completion.choices[0].message.content)

            # 使用expander组件显示当前输出，使其可折叠
            with st.expander(f"行 {index + 1} 的输出:"):
                # 显示输入内容
                st.write(combined_prompt)
                #分割线
                st.markdown("---")
                # 显示模型输出
                st.write(completion.choices[0].message.content)

        # 将结果保存到DataFrame
        df['GPT-3 Response'] = results

        # 完成后将进度条设置为100%
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
            # 处理全部数据
            processed_df = process_data(df, column_to_process, user_prompt)

            # 导出到Excel
            output_filename = 'processed_output.xlsx'
            processed_df.to_excel(output_filename, index=False)

            # 提供下载链接
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