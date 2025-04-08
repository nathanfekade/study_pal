import filetype
from django.core.exceptions import ValidationError

def validate_fIle_type(value):
    file_info = filetype.guess(value.file)
    if file_info is None:
        raise ValidationError('File type not Known')
    allowed_mime_types = ['application/pdf']
    if file_info.mime not in allowed_mime_types:
        raise ValidationError('only pdf and word files are allowed')