FROM python:3.11-slim
WORKDIR /app
COPY . /app
RUN pip install --upgrade pip
RUN pip install -e packages/markitdown[all]
RUN pip install streamlit

EXPOSE 8501

ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_PORT=8501

CMD ["python","-m","streamlit","run","apps/streamlit_app.py","--server.port","8501","--server.headless","true"]
