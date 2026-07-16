class SEOHeadersMiddleware:
    FILTER_PARAMS = {"brand", "color", "texture", "faktura", "offset"}
    PRIVATE_PREFIXES = (
        "/admin/",
        "/export_panel",
        "/PsstFuVvwLjdQvu",
        "/t3WNStJaz2N5Cuw",
        "/pnCne7xcIVMjG57",
        "/Nor2qRjFD3wbKiy",
        "/X5KD08OHn25yNLf",
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if self._should_noindex(request):
            response["X-Robots-Tag"] = "noindex, follow"
        return response

    def _should_noindex(self, request):
        path = request.path
        if any(path.startswith(prefix) for prefix in self.PRIVATE_PREFIXES):
            return True
        if path.startswith("/catalog/") and self.FILTER_PARAMS.intersection(request.GET):
            return True
        return False
