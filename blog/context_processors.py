# Контекстный процессор django

def custom_context(request):
    if hasattr(request, 'user'):
        can_share_recipe = request.user.is_authenticated
    else:
        can_share_recipe = False
    return {'can_share_recipe': can_share_recipe}
