import os
from django import template

register = template.Library()


@register.filter
def supabase_resize(url, dimensions):
    if not url or "supabase.co" not in url:
        return url

    try:
        width, height = dimensions.split("x")
        project_url = url.split("/storage/v1/object/public/")[0]
        remaining_path = url.split("/storage/v1/object/public/")[1]

        return f"{project_url}/storage/v1/render/image/public/{remaining_path}?width={width}&height={height}&resize=cover"
    except:
        return url
