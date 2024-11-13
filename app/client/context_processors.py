from .forms.postCreateForm import PostCreateForm  # Adjust the import path according to your project structure

def post_create_form(request):
    return {'post_create_form': PostCreateForm()}
