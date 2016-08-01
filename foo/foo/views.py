from django.shortcuts import render_to_response
from django.utils.safestring import mark_safe
from django.apps import apps

from tri.declarative import assert_kwargs_empty, collect_namespaces, setdefaults_path, dispatch, EMPTY
from tri.form.views import create_object, edit_object
from tri.struct import Struct, merged
from tri.table import render_table_to_response, Table, Link
import tri.table as tri_table
from tri.form import Field, bool_parse

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
class Column(tri_table.Column):
    # @staticmethod
    # def boolean_active_when_on(on_is=True, **kwargs):
    #     kwargs = setdefaults_path(
    #         Struct(),
    #         kwargs,
    #         query__show=True,
    #         query__gui__show=True,
    #         query__value_to_q=lambda variable, op, value_string_or_f: Q() if not value_string_or_f else Q(**{variable.attr: on_is})
    #     )
    #     return Column.from_model(**kwargs)

    @staticmethod
    def boolean_tri_state(**kwargs):
        kwargs = setdefaults_path(
            Struct(),
            kwargs,
            query__show=True,
            query__gui__show=True,
            query__gui__class=Field.choice,
            query__gui__choices=[True, False],
            query__gui__parse=lambda string_value, **_: bool_parse(string_value),
        )
        return Column.from_model(**kwargs)

    @staticmethod
    def freetext(**kwargs):
        return Column.from_model(**setdefaults_path(kwargs, query__show=True, query__freetext=True))


def all_models(request, **kwargs):
    kwargs = setdefaults_path(Struct(), kwargs)

    def data():
        for app_name, models in apps.all_models.items():
            for name, cls in models.items():
                if kwargs.get(app_name, {}).get(name, {}).get('show', True):
                    yield Struct(app_name=app_name, model_name=name, model=cls)

    class ModelsTable(Table):
        app_name = Column(auto_rowspan=True)
        model_name = Column(cell__url=lambda row, **_: '/triadmin/%s/%s/' % (row.app_name, row.model_name))

        class Meta:
            sortable = False

    result = render_table_to_response(
        request,
        template_name='base.html',
        table=ModelsTable(data=data()),
        paginate_by=None,
        **kwargs.pop('render_table', {}))
    return result


def list_model(request, app_name, model_name, **kwargs):
    kwargs = setdefaults_path(
        kwargs,
        table__data=apps.all_models[app_name][model_name].objects.all(),
        table__extra_fields=[Column.edit(after=0, cell__url=lambda row, **_: '%s/edit/' % row.pk)],
    )
    return render_table_to_response(
        request,
        template_name='base.html',
        links=[Link(title='Create %s' % model_name.replace('_', ' '), url='create/')],
        **kwargs)


@dispatch(
    all=EMPTY,
    list=EMPTY,
    create=EMPTY,
    edit=EMPTY,
)
def triadmin(request, app_name, model_name, pk, command, all, list, create, edit, **kwargs):
    kwargs = collect_namespaces(kwargs)
    all_models_kwargs = kwargs.pop('all_models', {})
    list_model_kwargs = kwargs.pop('list_model', {})
    create_object_kwargs = kwargs.pop('create_object', {})
    edit_object_kwargs = kwargs.pop('edit_object', {})

    def check_kwargs(kw):
        for app_name, model_names in kw.items():
            assert app_name in apps.all_models
            for model_name in model_names:
                assert model_name in apps.all_models[app_name]

    check_kwargs(list_model_kwargs)
    check_kwargs(create_object_kwargs)
    check_kwargs(edit_object_kwargs)

    if app_name is None and model_name is None:
        result = all_models(request, **merged(all, all_models_kwargs))

    elif command is None:
        assert pk is None
        result = list_model(request, app_name, model_name, **merged(list, list_model_kwargs.pop(app_name, {}).pop(model_name, {})))

    elif command == 'create':
        assert pk is None
        result = create_object(
            request,
            model=apps.all_models[app_name][model_name],
            render=render_to_response,
            **merged(create, create_object_kwargs.pop(app_name, {}).pop(model_name, {})))

    elif command == 'edit':
        assert pk
        result = edit_object(
            request,
            instance=apps.all_models[app_name][model_name].objects.get(pk=pk),
            render=render_to_response,
            **merged(edit, edit_object_kwargs.pop(app_name, {}).pop(model_name, {})))

    else:
        assert False, 'unknown command %s' % command

    assert_kwargs_empty(kwargs)
    return result


def triadmin_impl(request, **kwargs):
    return triadmin(request=request, **setdefaults_path(
        Struct(),
        kwargs,
        create__template_name='create_or_edit.html',
        edit__template_name='create_or_edit.html',
        all_models__sessions__session__show=False,
        list_model__auth__user__table__column=dict(
            is_superuser__class=Column.boolean_tri_state,
            is_staff__class=Column.boolean_tri_state,
            is_active__class=Column.boolean_tri_state,
            groups__query=dict(show=True, gui__show=True),
            email__class=Column.freetext,
            first_name__class=Column.freetext,
            last_name__class=Column.freetext,
        ),
        list_model__auth__user__table__column__password__show=False,
    ))
