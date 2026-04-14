import base64
import tempfile
from pathlib import Path

import flet as ft
import requests


def main(page: ft.Page):
    page.title = "UI"
    page.window_width = 1100
    page.window_height = 800
    page.scroll = ft.ScrollMode.AUTO

    api_url = ft.TextField(
        label="API URL",
        value="http://127.0.0.1:8000",
        width=400,
    )

    # Храним данные в памяти, чтобы можно было сохранить результат
    state = {
        "input_img_bytes": None,
        "output_img_bytes": None,
        "input_video_bytes": None,
        "output_video_bytes": None,
        "output_video_path": None,
        "save_type": None,  # "img" или "video"
    }

    # ---------- Картинки ----------
    image_input_name = ft.Text("Файл не выбран")
    image_input_preview = ft.Image(
        src="",
        width=450,
        height=320,
        fit="contain",
        border_radius=8,
    )
    image_output_preview = ft.Image(
        src="",
        width=450,
        height=320,
        fit="contain",
        border_radius=8,
    )
    image_description = ft.TextField(
        label="Описание от API",
        multiline=True,
        min_lines=3,
        max_lines=6,
        read_only=True,
        width=920,
    )

    # ---------- Видосики ----------
    video_input_name = ft.Text("Файл не выбран")
    video_output_name = ft.Text("Видео от API еще не получено")
    video_description = ft.TextField(
        label="Описание от API",
        multiline=True,
        min_lines=3,
        max_lines=6,
        read_only=True,
        width=920,
    )

    input_video_path_text = ft.Text("Путь входного видео: -")
    output_video_path_text = ft.Text("Путь выходного видео: -")

    def show_message(text: str, color: str = "blue"):
        page.snack_bar = ft.SnackBar(ft.Text(text), bgcolor=color)
        page.snack_bar.open = True
        page.update()

    def save_file_result(e: ft.FilePickerResultEvent):
        if not e.path:
            return

        save_path = Path(e.path)
        try:
            if state["save_type"] == "img" and state["output_img_bytes"] is not None:
                save_path.write_bytes(state["output_img_bytes"])
                show_message(f"Картинка сохранена: {save_path}", "green")
            elif state["save_type"] == "video" and state["output_video_bytes"] is not None:
                save_path.write_bytes(state["output_video_bytes"])
                show_message(f"Видео сохранено: {save_path}", "green")
            else:
                show_message("Нет данных для сохранения", "red")
        except Exception as ex:
            show_message(f"Ошибка сохранения: {ex}", "red")

    save_picker = ft.FilePicker(on_result=save_file_result)
    page.overlay.append(save_picker)

    # ---------------- Картинки ----------------
    def pick_image_result(e: ft.FilePickerResultEvent):
        if not e.files:
            return

        path = Path(e.files[0].path)
        image_input_name.value = f"Вход: {path.name}"
        state["input_img_bytes"] = path.read_bytes()

        image_input_preview.src_base64 = base64.b64encode(state["input_img_bytes"]).decode("utf-8")
        image_output_preview.src_base64 = None
        image_description.value = ""
        page.update()

    image_picker = ft.FilePicker(on_result=pick_image_result)
    page.overlay.append(image_picker)

    def send_image_to_api(_):
        if state["input_img_bytes"] is None:
            show_message("Сначала выбери картинку", "red")
            return

        try:
            show_message("Отправляю картинку в API...")
            payload = {"img": base64.b64encode(state["input_img_bytes"]).decode("utf-8")}
            resp = requests.post(f"{api_url.value}/img", json=payload, timeout=300)
            resp.raise_for_status()
            data = resp.json()

            out_b64 = data.get("img", "")
            description = data.get("description", "")
            state["output_img_bytes"] = base64.b64decode(out_b64)

            image_output_preview.src_base64 = out_b64
            image_description.value = description
            page.update()
            show_message("Готово", "green")
        except Exception as ex:
            show_message(f"Ошибка API: {ex}", "red")

    def save_image_result(_):
        if state["output_img_bytes"] is None:
            show_message("Нет картинки для сохранения", "red")
            return
        state["save_type"] = "img"
        save_picker.save_file(
            dialog_title="Сохранить картинку",
            file_name="result.jpg",
            allowed_extensions=["jpg", "jpeg", "png"],
        )

    # ---------------- Видосики ----------------
    def pick_video_result(e: ft.FilePickerResultEvent):
        if not e.files:
            return

        path = Path(e.files[0].path)
        video_input_name.value = f"Вход: {path.name}"
        state["input_video_bytes"] = path.read_bytes()

        input_video_path_text.value = f"Путь входного видео: {path}"
        output_video_path_text.value = "Путь выходного видео: -"
        video_output_name.value = "Видео от API еще не получено"
        video_description.value = ""
        page.update()

    video_picker = ft.FilePicker(on_result=pick_video_result)
    page.overlay.append(video_picker)

    def send_video_to_api(_):
        if state["input_video_bytes"] is None:
            show_message("Сначала выбери видео", "red")
            return

        try:
            show_message("Отправляю видео в API... Это может занять время.")
            payload = {"video": base64.b64encode(state["input_video_bytes"]).decode("utf-8")}
            resp = requests.post(f"{api_url.value}/video", json=payload, timeout=1800)
            resp.raise_for_status()
            data = resp.json()

            out_b64 = data.get("video", "")
            description = data.get("description", "")
            out_bytes = base64.b64decode(out_b64)
            state["output_video_bytes"] = out_bytes

            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
            temp_file.write(out_bytes)
            temp_file.close()

            state["output_video_path"] = temp_file.name
            video_output_name.value = f"Выход: {Path(temp_file.name).name}"
            output_video_path_text.value = f"Путь выходного видео: {temp_file.name}"
            video_description.value = description
            page.update()
            show_message("Готово", "green")
        except Exception as ex:
            show_message(f"Ошибка API: {ex}", "red")

    def save_video_result(_):
        if state["output_video_bytes"] is None:
            show_message("Нет видео для сохранения", "red")
            return
    def open_output_video(_):
        if not state["output_video_path"]:
            show_message("Сначала получи видео от API", "red")
            return
        video_path = Path(state["output_video_path"])
        if not video_path.exists():
            show_message("Файл выходного видео не найден", "red")
            return
        page.launch_url(video_path.as_uri())

        state["save_type"] = "video"
        save_picker.save_file(
            dialog_title="Сохранить видео",
            file_name="result.mp4",
            allowed_extensions=["mp4"],
        )

    # ---------- Макет ----------
    image_tab = ft.Tab(
        text="Картинки",
        content=ft.Container(
            padding=15,
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.ElevatedButton(
                                "Загрузить картинку",
                                on_click=lambda _: image_picker.pick_files(
                                    allow_multiple=False,
                                    allowed_extensions=["jpg", "jpeg", "png", "bmp"],
                                ),
                            ),
                            ft.ElevatedButton("Отправить в API", on_click=send_image_to_api),
                            ft.OutlinedButton("Сохранить результат", on_click=save_image_result),
                        ]
                    ),
                    image_input_name,
                    ft.Row(
                        controls=[
                            ft.Column([ft.Text("Вход"), image_input_preview]),
                            ft.Column([ft.Text("Выход"), image_output_preview]),
                        ],
                        spacing=20,
                    ),
                    image_description,
                ],
                spacing=12,
            ),
        ),
    )

    video_tab = ft.Tab(
        text="Видео",
        content=ft.Container(
            padding=15,
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.ElevatedButton(
                                "Загрузить видео",
                                on_click=lambda _: video_picker.pick_files(
                                    allow_multiple=False,
                                    allowed_extensions=["mp4", "avi", "mov", "mkv"],
                                ),
                            ),
                            ft.ElevatedButton("Отправить в API", on_click=send_video_to_api),
                            ft.OutlinedButton("Сохранить результат", on_click=save_video_result),
                        ]
                    ),
                    video_input_name,
                    video_output_name,
                    input_video_path_text,
                    output_video_path_text,
                    ft.ElevatedButton("Открыть выходное видео", on_click=open_output_video),
                    video_description,
                ],
                spacing=12,
            ),
        ),
    )

    page.add(
        ft.Column(
            controls=[
                ft.Text("UI для YOLO API", size=24, weight=ft.FontWeight.BOLD),
                api_url,
                ft.Tabs(
                    selected_index=0,
                    animation_duration=300,
                    tabs=[image_tab, video_tab],
                    expand=1,
                ),
            ],
            expand=True,
        )
    )


if __name__ == "__main__":
    ft.run(main)
