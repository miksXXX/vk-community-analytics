import streamlit.web.bootstrap as bootstrap
import sys

# Эти параметры обычно использует Streamlit
real_name = '__main__.py'  # Имя файла, который запускается
args = []
flag_options = {
    "server.port": 8000,
    "server.address": "0.0.0.0",
    "global.developmentMode": "false",
}

if __name__ == "__main__":
    # Запускаем Streamlit-приложение в том же процессе
    bootstrap.load_config_options(flag_options=flag_options)
    bootstrap._on_stop = lambda: None
    bootstrap._main(real_name, args, flag_options)
