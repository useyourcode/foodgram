import os

from fpdf import FPDF, HTMLMixin

from foodgram.settings import BASE_DIR

FONTS_DIR = BASE_DIR / 'recipes/data/fonts'


class PDF(FPDF, HTMLMixin):
    def __init__(self, title="Список покупок", *args, **kwargs):
        self.title = title
        super().__init__(*args, **kwargs)
        self._set_font()

    def _set_font(self) -> None:
        fonts = [
            ('Comic', '', 'COMIC.TTF'),
            ('Comic', 'B', 'COMICBD.TTF'),
            ('Comic', 'I', 'COMICI.TTF')
        ]
        for font in fonts:
            font_path = os.path.join(FONTS_DIR, font[2])
            if os.path.exists(font_path):
                self.add_font(font[0], style=font[1], fname=font_path)
            else:
                raise FileNotFoundError(f"Font file not found: {font_path}")
        self.set_font('Comic')

    def header(self) -> None:
        self.set_font('Comic', 'B', size=22)
        self.set_text_color(255, 255, 255)
        self.set_fill_color(0, 0, 0)
        self.rect(0, 0, 500, 25, style='F')
        self.cell(0, 7, self.title, align='C')
        self.ln(20)

    def footer(self) -> None:
        link = os.getenv('FOODGRAM_LINK')
        if link is None:
            return

        self.set_y(-15)
        self.set_text_color(128)
        text_link = link.split('://', 1)[-1]
        self.cell(0, 10, text_link, align='R', link=link)

    def get_pdf(self, html_text=None):
        if self.page == 0:
            self.add_page()
        if html_text is not None:
            self.write_html(html_text)
        return self.output()


def make_pdf_file(ingredients, recipes, request):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font('Comic', 'I', size=14)
    pdf.set_text_color(0, 0, 0)

    if recipes:
        pdf.cell(0, 10, 'Рецепты:', ln=True)
        for recipe in recipes:
            pdf.cell(
                0,
                6,
                recipe,
                align='L', border='B', new_x='LEFT', new_y='NEXT'
            )
        pdf.ln(6)

    pdf.set_font('Comic', 'B', size=12)
    pdf.cell(0, 10, 'Ингредиенты:', ln=True)
    pdf.set_font('Comic', '', size=12)
    for ingredient in ingredients:
        name = ingredient['name']
        unit = ingredient['unit']
        amount = ingredient['amount']
        pdf.cell(
            0, 6,
            f"{name} ({unit}) - {amount}",
            align='L', new_x='LEFT', new_y='NEXT'
        )
    pdf.ln(6)

    pdf_file = pdf.output(dest='S')
    return pdf_file
