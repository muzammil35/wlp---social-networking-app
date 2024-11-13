from django import forms


class RegisterForm(forms.Form):
    displayName = forms.CharField(label="Display Name", max_length=60)
    username = forms.CharField(label="Username", max_length=60)
    password = forms.CharField(
        label="Password", max_length=100, min_length=3, widget=forms.PasswordInput)
    confirmPassword = forms.CharField(
        label="Confirm Password", max_length=100, min_length=3, widget=forms.PasswordInput)

    github = forms.URLField(label="Github", max_length=200, required=False)
    profileImage = forms.URLField(
        label="Profile Image", max_length=200, required=False)

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirmPassword = cleaned_data.get("confirmPassword")

        if password != confirmPassword:
            raise forms.ValidationError("Passwords do not match")
        return cleaned_data


class ProfileEditForm(forms.Form):
    displayName = forms.CharField(label="Display Name", max_length=60)
    github = forms.URLField(label="Github", max_length=200, required=False)
    profileImage = forms.URLField(
        label="Profile Image", max_length=200, required=False)
