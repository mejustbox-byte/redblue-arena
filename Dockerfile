FROM python:3.12-slim
WORKDIR /app
COPY redblue_arena /app/redblue_arena
COPY examples/lab.json /app/examples/lab.json
USER 65532:65532
ENTRYPOINT ["python", "-m", "redblue_arena"]
CMD ["--config", "examples/lab.json"]
