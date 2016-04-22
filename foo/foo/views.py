from django.shortcuts import render_to_response
from django.utils.safestring import mark_safe
from django.apps import apps
from tri.form.views import create_object, edit_object
from tri.struct import Struct
from tri.table import render_table_to_response, Table, Column, Link

from foo.models import Person


def example1(request):
    return render_table_to_response(
        request,
        table__data=Person.objects.all())


def example2(request):
    return render_table_to_response(
        request,
        table__data=Person.objects.all(),
        table__column__id__show=True)


def example3(request):
    return render_table_to_response(
        request,
        table__data=Person.objects.all(),
        table__column__last_name__cell__format=lambda value, **_: mark_safe('<h1>hello %s!</h1>' % value))


def example4(request):
    request.user.is_admin = True
    request.user.is_staff = True
    return render_table_to_response(
        request,
        table__data=Person.objects.all(),
        table__column__id__show=lambda table, **_: table.request.user.is_staff,
        table__column__last_name__show=lambda table, **_: table.request.user.is_admin)


def example5(request):
    class PersonTable(Table):
        class Meta:
            model = Person
            columns = Table.columns_from_model(
                model=Person,
                column__id__show=lambda table, **_: table.request.user.is_staff,
                column__last_name__show=lambda table, **_: table.request.user.is_admin)

    request.user.is_admin = True
    request.user.is_staff = True
    return render_table_to_response(request, table=PersonTable())


# -----
def all_models(request):
    def data():
        for app_name, models in apps.all_models.items():
            for name, cls in models.items():
                yield Struct(app_name=app_name, model_name=name, model=cls)

    class ModelsTable(Table):
        app_name = Column(auto_rowspan=True)
        model_name = Column(cell__url=lambda row, **_: '/triadmin/%s/%s/' % (row.app_name, row.model_name))

        class Meta:
            sortable = False

    return render_table_to_response(
        request,
        template_name='base.html',
        table=ModelsTable(data=data()),
        paginate_by=None)


def list_model(request, app_name, model_name):
    return render_table_to_response(
        request,
        template_name='base.html',
        links=[Link(title='Create %s' % model_name.replace('_', ' '), url='create/')],
        table__data=apps.all_models[app_name][model_name].objects.all(),
        table__extra_fields=[Column.edit(after=0, cell__url=lambda row, **_: '%s/edit/' % row.pk)])


def triadmin(request, app_name, model_name, pk, command):
    if app_name is None and model_name is None:
        return all_models(request)

    if command is None:
        return list_model(request, app_name, model_name)

    if pk is None and command == 'create':
        return create_object(
            request,
            model=apps.all_models[app_name][model_name],
            render=render_to_response)

    assert pk and command == 'edit'

    return edit_object(
        request,
        instance=apps.all_models[app_name][model_name].objects.get(pk=pk),
        render=render_to_response)
