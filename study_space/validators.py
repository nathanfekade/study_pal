import filetype
from django.core.exceptions import ValidationError
from pypdf import PdfReader

def validate_fIle_size_and_type(value):
    file_info = filetype.guess(value.file)
    if file_info is None:
        raise ValidationError('File type not Known')
    allowed_mime_types = ['application/pdf']
    if file_info.mime not in allowed_mime_types:
        raise ValidationError('only pdf and word files are allowed')
    
    try:
        value.file.seek(0)
        pdf = PdfReader(value.file)
        num_pages = len(pdf.pages)
        if num_pages > 100:
            raise ValidationError('PDF file must not be greater than 100 pages')
    
    except Exception as e:
        raise ValidationError(f'{str(e)}')