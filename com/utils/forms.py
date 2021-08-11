from django import forms


class PaginationForm(forms.Form):
    offset = forms.IntegerField(required=False, min_value=0)
    limit = forms.IntegerField(required=False, min_value=1)

    def is_valid(self):
        result = super().is_valid()
        if self.cleaned_data.get("offset") is None:
            self.cleaned_data["offset"] = 0
        if self.cleaned_data.get("limit") is None:
            self.cleaned_data["limit"] = 1
        self.cleaned_data["limit"] = min(self.cleaned_data["limit"], 50)
        return result
