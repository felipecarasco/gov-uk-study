from flask_wtf import FlaskForm
from govuk_frontend_wtf.wtforms_widgets import (
    GovRadioInput,
    GovSubmitInput,
    GovTextArea,
    GovTextInput,
)
from wtforms import RadioField, StringField, SubmitField, TextAreaField
from wtforms.validators import AnyOf, DataRequired, Email, InputRequired, Length

# Values match the DocumentType enum on the Java side, which is what the API accepts.
DOCUMENT_TYPES = [
    ("TITLE_REGISTER", "Title register"),
    ("TITLE_PLAN", "Title plan"),
]

# Label for each stored value, shared by the radios and the check answers page
# so the two cannot drift apart.
DOCUMENT_TYPE_LABELS = dict(DOCUMENT_TYPES)

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


def _trim(value):
    return value.strip() if isinstance(value, str) else value


def _trim_lower(value):
    return value.strip().lower() if isinstance(value, str) else value


class YourDetailsForm(FlaskForm):
    # Fields are declared in page order: the error summary lists them in this order.
    #
    # DataRequired rather than InputRequired: it checks the value after the
    # filters, so a field of only spaces, trimmed to "", counts as empty.
    applicant_name = StringField(
        "Full name",
        widget=GovTextInput(),
        filters=[_trim],
        validators=[
            DataRequired(message="Enter your full name"),
            Length(max=255, message="Full name must be 255 characters or fewer"),
        ],
    )

    applicant_email = StringField(
        "Email address",
        widget=GovTextInput(),
        filters=[_trim_lower],
        validators=[
            DataRequired(message="Enter your email address"),
            Email(message="Enter an email address in the correct format, like name@example.com"),
        ],
    )

    applicant_address = TextAreaField(
        "Address",
        widget=GovTextArea(),
        filters=[_trim],
        validators=[DataRequired(message="Enter your address")],
    )

    submit = SubmitField("Continue", widget=GovSubmitInput())


class ConfirmOrderForm(FlaskForm):
    """Only a button, but a FlaskForm so that the CSRF token is checked.

    Without it, any other site could post to this page using the visitor's
    session and place an order in their name.
    """

    submit = SubmitField("Accept and continue to payment", widget=GovSubmitInput())


class PaymentForm(FlaskForm):
    """Only the Pay button, but a FlaskForm so that the CSRF token is checked."""

    submit = SubmitField("Pay", widget=GovSubmitInput())
