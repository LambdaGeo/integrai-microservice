from django import template

register = template.Library()



@register.filter(name='add_class')
def add_class(field, css):
    return field.as_widget(attrs={"class": css})

@register.filter
def multiply(value, arg):
    print (value, arg)
    return value * arg if value is not None and arg is not None else 0


@register.filter
def abs(value):
    try:
        return abs(value)
    except:
        return value
    
@register.filter(name='add_class')
def add_class(field, css_class):
    return field.as_widget(attrs={"class": css_class})



@register.filter
def add_placeholder(field, placeholder_text):
    return field.as_widget(attrs={"placeholder": placeholder_text})


@register.filter
def add_attrs(field, args):
    """
    Adiciona atributos ao campo de formulário.
    Ex: {{ field|add_attrs:"class=form-control,placeholder=Digite aqui" }}
    """
    attrs = {}
    for arg in args.split(','):
        if '=' in arg:
            key, val = arg.split('=')
            attrs[key.strip()] = val.strip()
    return field.as_widget(attrs=attrs)