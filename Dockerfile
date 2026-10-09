FROM python:3.12-slim
WORKDIR /app
COPY redblue_arena /app/redblue_arena
COPY examples /app/examples
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1
USER 65532:65532
ENTRYPOINT ["python", "-m", "redblue_arena"]
CMD ["--config", "examples/lab.json"]
