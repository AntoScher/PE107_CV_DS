import streamlit as st
from deepseek_api import DeepSeekAPI
from parse_hh import get_html, extract_vacancy_data, extract_resume_data

# Initialize DeepSeek client
client = DeepSeekAPI(api_key=st.secrets["DEEPSEEK_API_KEY"])

SYSTEM_PROMPT = """
Проскорь кандидата, насколько он подходит для данной вакансии.

Сначала напиши короткий анализ, который будет пояснять оценку.
Отдельно оцени качество заполнения резюме (понятно ли, с какими задачами сталкивался кандидат и каким образом их решал?). Эта оценка должна учитываться при выставлении финальной оценки - нам важно нанимать таких кандидатов, которые могут рассказать про свою работу
Потом представь результат в виде оценки от 1 до 10.
""".strip()

def request_deepseek(system_prompt, user_prompt):
    response = client.chat(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        max_tokens=1000,
        temperature=0,
    )
    return response.choices[0].message.content

# UI
st.title('CV Scoring App')

job_description = st.text_area('Введите ссылку на вакансию')
cv = st.text_area('Введите ссылку на резюме')

if st.button("Проанализировать соответствие"):
    with st.spinner("Парсим данные и отправляем в GPT..."):
        try:
            job_html = get_html(job_description).text
            resume_html = get_html(cv).text

            job_text = extract_vacancy_data(job_html)
            resume_text = extract_resume_data(resume_html)

            prompt = f"# ВАКАНСИЯ\n{job_text}\n\n# РЕЗЮМЕ\n{resume_text}"
            response = request_deepseek(SYSTEM_PROMPT, prompt)

            st.subheader("📊 Результат анализа:")
            st.markdown(response)

        except Exception as e:
            st.error(f"Произошла ошибка: {e}")
