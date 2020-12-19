from django.forms import ClearableFileInput
from django.template.loader import render_to_string


class PreviewClearableFileInput(ClearableFileInput):
    template_name = "widgets/preview_clearable_file_input.html"

    class Media:
        js = [
            "https://code.jquery.com/jquery-3.4.1.min.js",
        ]


class PreviewImageFileWidget(ClearableFileInput):
    # 아래와 같이 템플릿을 지정해서 구현할수도 있습니다. 여기서는 render_to_string을 쓸 예정이니 주석처리
    # template_name = "widgets/preview_imagefile_widget.html"

    # 아래와 같이 js코드 링크를 불러올수도 있습니다. 여기서는 이 방법은 안쓰니 주석처리
    # class Media:
    #     js = [
    #         'https://code.jquery.com/jquery-3.4.1.min.js'
    #     ]

    #############################################
    # render 함수를 오버라이딩 해줍니다.
    #############################################
    # -- value는 이미지가 들어갑니다. (여기서는 ClearableFileInput이므로)
    # -- name은 ClearableFileInput이 적용되는 우리 폼의 imagefield 이름이 들어갑니다. 이 이름은 우리가 PreviewImageFileWidget을 쓸 HTML코드에 있겠죠?
    # -- attrs에는 id 등의 값이 dict 형태로 들어갑니다.
    ##############################################

    def render(self, name, value, attrs=None, renderer=None):
        # 커스텀 위젯 템플릿으로 전달할 context를 만들어주고
        context = {"value": value, "name": name, "id": attrs["id"]}
        # render_to_string을 이용해 HTML코드와 context를 잘 버무려줍니다.
        html = render_to_string("widgets/preview_imagefile_widget.html", context)

        # 아래 코드를 통해 상속받은 위젯의 HTML코드를 불러울 수 있습니다.
        # parent_html = super().render(name, value, attrs, renderer)

        # 또 아래와 같이 .py 코드에서 스크립트를 짜서 동작토록 할수도 있습니다.
        # 이렇게 하려면 아래 return html + inline_code 이런식으로 하면 되겠죠?
        # inline_code = mark_safe(
        #    <script>
        #        $('.btn').change(function() {
        #            alert('테스트');
        #        });
        #    </script>
        # )

        # 그리고 return 해주면 끝
        return html