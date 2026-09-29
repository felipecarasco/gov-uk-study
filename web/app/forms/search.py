from flask_wtf import FlaskForm
from govuk_frontend_wtf.wtforms_widgets import GovSubmitInput, GovTextInput
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, InputRequired, Regexp, ValidationError

from app import postcodes

# HMLR title numbers: a 2 or 3 letter registry prefix followed by 4 to 6
# digits. For example SGL123456, MX987654.
TITLE_NUMBER_PATTERN = r"^[A-Z]{2,3}\d{4,6}$"


def _upper_trim(value):
    return value.strip().upper() if isinstance(value, str) else value


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


def _trim(value):
    return value.strip() if isinstance(value, str) else value


def _full_postcode(form, field):
    if not postcodes.is_valid(field.data):
        raise ValidationError("Enter a full postcode, like CR0 2QQ")


class PostcodeForm(FlaskForm):
    # DataRequired, not InputRequired: after the trim filter, "   " is empty.
    postcode = StringField(
        "Postcode",
        widget=GovTextInput(),
        filters=[_trim],
        validators=[DataRequired(message="Enter a postcode"), _full_postcode],
    )

    submit = SubmitField("Search", widget=GovSubmitInput())
