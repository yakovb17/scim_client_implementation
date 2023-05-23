from django.http import HttpResponse, HttpResponseForbidden, JsonResponse, HttpResponseNotFound
from django.views import View
from django.views.decorators.http import require_GET
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404
from typing import Tuple, Union
import jwt
import json

from .models import Employee

JWT_TOKEN_PAYLOAD = 'secret'


class ScimService(View):
    """
    View for Users provisioning
    """
        
    def get(self, request) -> HttpResponse:
        is_auth, payload = self._authenticate()

        if not is_auth:
            return HttpResponseForbidden()
        
        if 'filter' in request.GET:
            return self._handle_get_by_query()
        else:
            return self._handle_get_by_id()

    def post(self, request) -> HttpResponse:
        is_auth, payload = self._authenticate()
        if not is_auth:
            return HttpResponseForbidden()
        
        data = json.loads(request.body)
        new_employee = Employee()
        new_employee.username = data.get('userName')
        new_employee.meta = json.dumps(data.get('meta'))
        new_employee.save()

        resp_data = self._create_scim_response_single_employee(new_employee)
        resp = JsonResponse(resp_data, safe=False)
        resp.status_code = 201

        return resp

    def patch(self, request) -> HttpResponse:
        is_auth, payload = self._authenticate()

        if not is_auth:
            return HttpResponseForbidden()
        
        employee_id = request.path.split('/')[-1]
        req_data = json.loads(request.body)

        try:
            employee = Employee.objects.get(id=employee_id)
        except ObjectDoesNotExist:
            return HttpResponseNotFound()
        
        need_to_save_changes = False
        for operation in req_data.get('Operations', []):
            if operation['op'].lower() == 'replace':
                need_to_save_changes = self._update_employee(employee, operation['path'], operation['value'])
        
        if need_to_save_changes:
            employee.save()

        return JsonResponse(self._create_scim_response_single_employee(employee))

    def delete(self, request) -> HttpResponse:
        is_auth, payload = self._authenticate()
        if not is_auth:
            return HttpResponseForbidden()
        
        userid = self.request.path.split('/')[-1]

        try:
            deleted = Employee.objects.get(id=userid).delete()
        except ObjectDoesNotExist as e:
            print(e)
            return HttpResponseNotFound()
        
        res = HttpResponse()
        res.status_code = 204
        return res

    def _authenticate(self) -> Tuple[bool, Union[dict, None]]:
        
        is_auth = False
        payload = None
        token = self.request.headers.get('Authorization', '').replace('Bearer ', '')
        if token:
            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms="HS256")
                is_auth = True
            except Exception as e:
                pass
        return is_auth, payload

    def _handle_get_by_id(self) -> HttpResponse:
        path = self.request.path.split('/')
        userid = path[-1]
        res = get_object_or_404(Employee, pk=userid)
        
        res = res.serialize()
        return JsonResponse(res)

    def _handle_get_by_query(self) -> HttpResponse:
        username = self._extract_username_from_query_param()
        employees = Employee.objects.filter(username=username)
        res = self._create_scim_response_multiple_employees(employees)
        return JsonResponse(res, safe=False)

    def _extract_username_from_query_param(self) -> Union[str, None]:
        query_param_val = self.request.GET['filter']        
        username = query_param_val.replace('userName eq ', '')
        if username.startswith('"'):
            username = username[1:-1]
        if username.endswith('"'):
            username = username[0:-2]

        return username

    @staticmethod
    def _update_employee(employee: Employee, path: str, value) -> bool:
        employee_data_changed = True

        path = path.lower()

        if path == 'username':
            employee.username = value
        elif path == 'meta':
            employee.meta = json.dumps(value)
        else: # if path does not have relevant field in Employee
            employee_data_changed = False
        
        return employee_data_changed
      
    @staticmethod
    def _create_scim_response_single_employee(employee) -> dict:
        res = {
                "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
                "id": employee.id,
                "meta": {
                    "resourceType": "User",
                    "created": employee.created_at,
                    "lastModified": employee.updated_at,
                },
                "userName": employee.username,
        }
        return res
    
    def _create_scim_response_multiple_employees(self, employees_lst: list) -> dict:
        res = {
                "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
                "totalResults": len(employees_lst),
                "Resources": [self._create_scim_response_single_employee(employee) for employee in employees_lst]
            }
        
        return res
        

@require_GET
def get_scim_token(request) -> JsonResponse:
    token = jwt.encode({"customer_id": JWT_TOKEN_PAYLOAD}, settings.SECRET_KEY, algorithm="HS256")
    return JsonResponse({"token": token})
