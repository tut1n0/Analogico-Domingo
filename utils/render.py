from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")


def render(request, template, context=None):

    if context is None:
        context = {}

    context["session"] = request.session

    return templates.TemplateResponse(
        request=request,
        name=template,
        context=context
    )