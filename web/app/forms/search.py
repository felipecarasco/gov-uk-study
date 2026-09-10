from flask_wtf import FlaskForm
from govuk_frontend_wtf.wtforms_widgets import GovSubmitInput, GovTextInput
from wtforms import StringField, SubmitField
from wtforms.validators import InputRequired, Regexp

# Números de título do HMLR: 2 ou 3 letras de prefixo do registro,
# seguidas de 4 a 6 dígitos. Ex.: SGL123456, MX987654.
TITLE_NUMBER_PATTERN = r"^[A-Z]{2,3}\d{4,6}$"


def _upper_trim(valor):
    return valor.strip().upper() if isinstance(valor, str) else valor


class TitleNumberForm(FlaskForm):
    title_number = StringField(
        "Title number",
        widget=GovTextInput(),
        filters=[_upper_trim],
        validators=[
            InputRequired(message="Enter a title number"),
            Regexp(
                TITLE_NUMBER_PATTERN,
                message="Enter a title number in the correct format, like SGL123456",
            ),
        ],
        description="For example, SGL123456",
    )

    submit = SubmitField("Continue", widget=GovSubmitInput())
