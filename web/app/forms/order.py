from flask_wtf import FlaskForm
from govuk_frontend_wtf.wtforms_widgets import GovRadioInput, GovSubmitInput
from wtforms import RadioField, SubmitField
from wtforms.validators import AnyOf, InputRequired

# Values match the DocumentType enum on the Java side, which is what the API accepts.
DOCUMENT_TYPES = [
    ("TITLE_REGISTER", "Title register"),
    ("TITLE_PLAN", "Title plan"),
]

_SELECT_A_DOCUMENT_TYPE = "Select a document type"


class DocumentTypeForm(FlaskForm):
    # validate_choice=False turns off RadioField's built-in check, whose message
    # ("Not a valid choice.") is not GOV.UK wording. AnyOf does the same check
    # with the right message.
    document_type = RadioField(
        "What do you want to order?",
        widget=GovRadioInput(),
        choices=DOCUMENT_TYPES,
        validate_choice=False,
        validators=[
            InputRequired(message=_SELECT_A_DOCUMENT_TYPE),
            AnyOf([value for value, _ in DOCUMENT_TYPES], message=_SELECT_A_DOCUMENT_TYPE),
        ],
    )

    submit = SubmitField("Continue", widget=GovSubmitInput())
