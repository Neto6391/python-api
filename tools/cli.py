
from __future__ import annotations

import re
import textwrap
from pathlib import Path
from typing import List, Tuple

import typer

APP_ROOT = Path(__file__).resolve().parents[1]  # project root (where app/ lives)
app = typer.Typer(help="CLI para gerar endpoints, controllers, entidades e DI automaticamente.")

def snake(name: str) -> str:
    s = re.sub(r"[\s\-]+", "_", name.strip())
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s).lower()
    return s

def pascal(name: str) -> str:
    parts = re.split(r"[_\-\s]+", name.strip())
    return "".join(p.capitalize() for p in parts if p)

def parse_fields(fields_str: str) -> List[Tuple[str, str]]:
    """
    Ex.: "title:str, pages:int, price:float, published:bool"
    """
    if not fields_str.strip():
        return []
    pairs = []
    for chunk in fields_str.split(","):
        if not chunk.strip():
            continue
        if ":" not in chunk:
            raise typer.BadParameter(f"Campo inválido: '{chunk}'. Formato esperado: nome:tipo")
        name, typ = chunk.split(":", 1)
        name = snake(name.strip())
        typ = typ.strip()
        if typ not in {"str", "int", "float", "bool"}:
            raise typer.BadParameter(f"Tipo inválido '{typ}' para '{name}'. Use: str, int, float, bool")
        pairs.append((name, typ))
    return pairs

def append_once(path: Path, needle: str, block: str) -> None:
    """
    Adiciona 'block' ao final do arquivo se 'needle' não existir.
    """
    text = path.read_text(encoding="utf-8")
    if needle in text:
        return
    with path.open("a", encoding="utf-8") as f:
        f.write("\n" + block.strip() + "\n")

def insert_in_container(path: Path, needle: str, imports_block: str, providers_block: str) -> None:
    """
    Insere imports no topo e providers dentro da classe Container.
    """
    text = path.read_text(encoding="utf-8")
    if needle in text:
        return
    
    lines = text.split('\n')
    
    # Encontrar onde inserir imports (após os imports existentes)
    import_insert_idx = 0
    for i, line in enumerate(lines):
        if line.startswith('from ') or line.startswith('import '):
            import_insert_idx = i + 1
    
    # Encontrar onde inserir providers (dentro da classe Container, após o último provider)
    provider_insert_idx = len(lines)
    in_container_class = False
    
    for i, line in enumerate(lines):
        if 'class Container(' in line:
            in_container_class = True
        elif in_container_class and line.strip().startswith('providers.Singleton'):
            provider_insert_idx = i + 1
    
    # Inserir imports
    lines.insert(import_insert_idx, imports_block)
    
    # Inserir providers (ajustar índice devido à inserção anterior)
    lines.insert(provider_insert_idx + 1, providers_block)
    
    # Escrever arquivo
    path.write_text('\n'.join(lines), encoding='utf-8')


@app.callback(invoke_without_command=True)
def scaffold(
    resource: str = typer.Option(..., "--resource", "-r", help="Nome lógico do recurso (ex.: book)"),
    endpoint_path: str = typer.Option(..., "--path", "-p", help="Caminho do endpoint (ex.: /books)"),
    methods: str = typer.Option("GET,POST,PUT,DELETE", "--methods", "-m", help="Lista separada por vírgulas"),
    fields: str = typer.Option("", "--fields", "-f", help="Campos nome:tipo"),
    component: str = typer.Option("full", "--component", "-c", help="Componente a gerar: model, usecase, endpoints, adapter, full"),
):
    """
    Gera estrutura mínima para novo recurso seguindo a arquitetura do projeto:
    - Domain: entidade e (opcional) port
    - Application: DTO, Mapper, UseCases básicos
    - Infrastructure: Adapter stub
    - Presentation: Schemas, Controller e Endpoints
    - DI: registra providers no container
    - API Router: inclui o router novo
    """
    # Validação de componente
    valid_components = {"model", "usecase", "endpoints", "adapter", "full"}
    if component not in valid_components:
        raise typer.BadParameter(f"Componente inválido: {component}. Use: {', '.join(valid_components)}")
    
    resource_snake = snake(resource)
    resource_pascal = pascal(resource)
    feature_dir = APP_ROOT / "app" / "presentation" / "v1" / "endpoints" / resource_snake

    meths = [m.strip().upper() for m in methods.split(",") if m.strip()]
    valid = {"GET", "POST", "PUT", "DELETE"}
    for m in meths:
        if m not in valid:
            raise typer.BadParameter(f"Método inválido: {m}. Use GET, POST, PUT ou DELETE.")
    if not meths:
        raise typer.BadParameter("Informe pelo menos um método em --methods.")

    fields_list = parse_fields(fields)
    print(f"DEBUG: resource_snake={resource_snake}, fields_list={fields_list}, component={component}")

    # --- Domain (Model) ---
    if component in ["model", "full"]:
        domain_base = APP_ROOT / "app" / "domain" / resource_snake
        print(f"DEBUG: domain_base={domain_base}")
        entities_dir = domain_base / "entities"
        ports_dir = domain_base / "ports"
        entities_dir.mkdir(parents=True, exist_ok=True)
        ports_dir.mkdir(parents=True, exist_ok=True)

        entity_code = [
            "from dataclasses import dataclass",
            "from typing import Optional",
            "",
            "@dataclass",
            f"class {resource_pascal}:",
        ]
        if fields_list:
            for name, typ in fields_list:
                py_typ = {"str":"str","int":"int","float":"float","bool":"bool"}[typ]
                entity_code.append(f"    {name}: {py_typ}")
        entity_code.append("    id: Optional[str] = None")
        (entities_dir / f"{resource_snake}.py").write_text("\n".join(entity_code) + "\n", encoding="utf-8")

        port_code = textwrap.dedent(f"""
        from typing import Protocol, List, Optional
        from app.domain.{resource_snake}.entities.{resource_snake} import {resource_pascal}

        class {resource_pascal}Port(Protocol):
            def get_all(self) -> List[{resource_pascal}]: ...
            def get_one(self, identifier: str) -> Optional[{resource_pascal}]: ...
            def create(self, entity: {resource_pascal}) -> {resource_pascal}: ...
            def update(self, identifier: str, entity: {resource_pascal}) -> {resource_pascal}: ...
            def delete(self, identifier: str) -> None: ...
        """).strip() + "\n"
        (ports_dir / f"{resource_snake}_port.py").write_text(port_code, encoding="utf-8")

    # --- Application (DTO, Mapper, UseCases) ---
    if component in ["usecase", "full"]:
        app_base = APP_ROOT / "app" / "application" / resource_snake
        dtos_dir = app_base / "dtos"
        mappers_dir = app_base / "mappers"
        use_cases_dir = app_base / "use_cases"
        dtos_dir.mkdir(parents=True, exist_ok=True)
        mappers_dir.mkdir(parents=True, exist_ok=True)
        use_cases_dir.mkdir(parents=True, exist_ok=True)

        # DTO
        if fields_list:
            dto_fields_lines = [f"    {name}: { {'str':'str','int':'int','float':'float','bool':'bool'}[typ] }" for name, typ in fields_list]
            dto_fields_str = "\n".join(dto_fields_lines)
            dto_code = f"""from dataclasses import dataclass
from typing import Optional

@dataclass
class {resource_pascal}DTO:
{dto_fields_str}
    id: Optional[str] = None
"""
        else:
            dto_code = textwrap.dedent(f"""
            from dataclasses import dataclass
            from typing import Optional

            @dataclass
            class {resource_pascal}DTO:
                id: Optional[str] = None
            """).strip() + "\n"
        (dtos_dir / f"{resource_snake}_dto.py").write_text(dto_code, encoding="utf-8")

        # Mapper
        mapper_code = textwrap.dedent(f"""
        from dataclasses import asdict
        from app.domain.{resource_snake}.entities.{resource_snake} import {resource_pascal}
        from app.application.{resource_snake}.dtos.{resource_snake}_dto import {resource_pascal}DTO

        class {resource_pascal}Mapper:
            @staticmethod
            def to_dto(entity: {resource_pascal}) -> {resource_pascal}DTO:
                return {resource_pascal}DTO(**asdict(entity))

            @staticmethod
            def to_domain(dto: {resource_pascal}DTO) -> {resource_pascal}:
                return {resource_pascal}(**asdict(dto))
        """).strip() + "\n"
        (mappers_dir / f"{resource_snake}_mapper.py").write_text(mapper_code, encoding="utf-8")

        # UseCases (básicos conforme métodos)
        uc_templates = {}
        if "GET" in meths:
            uc_templates["list"] = textwrap.dedent(f"""
            from typing import List
            from app.domain.{resource_snake}.ports.{resource_snake}_port import {resource_pascal}Port
            from app.domain.{resource_snake}.entities.{resource_snake} import {resource_pascal}

            class List{resource_pascal}UseCase:
                def __init__(self, port: {resource_pascal}Port) -> None:
                    self._port = port

                def execute(self) -> List[{resource_pascal}]:
                    return self._port.get_all()
            """).strip() + "\n"
            uc_templates["get"] = textwrap.dedent(f"""
            from app.domain.{resource_snake}.ports.{resource_snake}_port import {resource_pascal}Port
            from app.domain.{resource_snake}.entities.{resource_snake} import {resource_pascal}
            from typing import Optional

            class Get{resource_pascal}UseCase:
                def __init__(self, port: {resource_pascal}Port) -> None:
                    self._port = port

                def execute(self, identifier: str) -> Optional[{resource_pascal}]:
                    return self._port.get_one(identifier)
            """).strip() + "\n"
        if "POST" in meths:
            uc_templates["create"] = textwrap.dedent(f"""
            from app.domain.{resource_snake}.ports.{resource_snake}_port import {resource_pascal}Port
            from app.domain.{resource_snake}.entities.{resource_snake} import {resource_pascal}

            class Create{resource_pascal}UseCase:
                def __init__(self, port: {resource_pascal}Port) -> None:
                    self._port = port

                def execute(self, entity: {resource_pascal}) -> {resource_pascal}:
                    return self._port.create(entity)
            """).strip() + "\n"
        if "PUT" in meths:
            uc_templates["update"] = textwrap.dedent(f"""
            from app.domain.{resource_snake}.ports.{resource_snake}_port import {resource_pascal}Port
            from app.domain.{resource_snake}.entities.{resource_snake} import {resource_pascal}

            class Update{resource_pascal}UseCase:
                def __init__(self, port: {resource_pascal}Port) -> None:
                    self._port = port

                def execute(self, identifier: str, entity: {resource_pascal}) -> {resource_pascal}:
                    return self._port.update(identifier, entity)
            """).strip() + "\n"
        if "DELETE" in meths:
            uc_templates["delete"] = textwrap.dedent(f"""
            from app.domain.{resource_snake}.ports.{resource_snake}_port import {resource_pascal}Port

            class Delete{resource_pascal}UseCase:
                def __init__(self, port: {resource_pascal}Port) -> None:
                    self._port = port

                def execute(self, identifier: str) -> None:
                    self._port.delete(identifier)
            """).strip() + "\n"

        for name, code in uc_templates.items():
            (use_cases_dir / f"{name}_{resource_snake}.py").write_text(code, encoding="utf-8")

    # --- Infrastructure (Adapter stub em memória) ---
    if component in ["adapter", "full"]:
        infra_dir = APP_ROOT / "app" / "infrastructure" / resource_snake / "adapters"
        infra_dir.mkdir(parents=True, exist_ok=True)
        adapter_code = textwrap.dedent(f"""
        from typing import List, Optional
        from app.domain.{resource_snake}.entities.{resource_snake} import {resource_pascal}
        from app.domain.{resource_snake}.ports.{resource_snake}_port import {resource_pascal}Port
        from app.core.config.logging import get_logger

        logger = get_logger(__name__)

        class InMemory{resource_pascal}Adapter({resource_pascal}Port):
            def __init__(self) -> None:
                self._items: List[{resource_pascal}] = []
                self._next_id: int = 1

            def get_all(self) -> List[{resource_pascal}]:
                logger.debug("InMemory{resource_pascal}Adapter.get_all")
                return list(self._items)

            def get_one(self, identifier: str) -> Optional[{resource_pascal}]:
                logger.debug("InMemory{resource_pascal}Adapter.get_one: %s", identifier)
                return next((x for x in self._items if getattr(x, "id", None) == identifier), None)

            def create(self, entity: {resource_pascal}) -> {resource_pascal}:
                logger.debug("InMemory{resource_pascal}Adapter.create: %s", entity)
                entity.id = str(self._next_id)
                self._next_id += 1
                self._items.append(entity)
                return entity

            def update(self, identifier: str, entity: {resource_pascal}) -> {resource_pascal}:
                logger.debug("InMemory{resource_pascal}Adapter.update: %s", identifier)
                idx = next((i for i, x in enumerate(self._items) if getattr(x, "id", None) == identifier), None)
                if idx is None:
                    self._items.append(entity)
                    return entity
                self._items[idx] = entity
                return entity

            def delete(self, identifier: str) -> None:
                logger.debug("InMemory{resource_pascal}Adapter.delete: %s", identifier)
                self._items = [x for x in self._items if getattr(x, "id", None) != identifier]
        """).strip() + "\n"
        (infra_dir / f"in_memory_{resource_snake}_adapter.py").write_text(adapter_code, encoding="utf-8")

    # --- Presentation (Schemas, Controller e Endpoints) ---
    if component in ["endpoints", "full"]:
        schemas_dir = APP_ROOT / "app" / "presentation" / "v1" / "schemas"
        controller_path = feature_dir / "controller.py"
        endpoints_path = feature_dir / "endpoints.py"
        feature_dir.mkdir(parents=True, exist_ok=True)

        # Schemas
        req_schema_name = f"{resource_pascal}Request"
        res_schema_name = f"{resource_pascal}Response"

        req_fields = "\n".join([f"    {n}: {t}" for n, t in fields_list]) if fields_list else "    pass"
        res_fields = "\n".join([f"    {n}: {t}" for n, t in fields_list]) if fields_list else "    pass"
        if fields_list:
            res_fields = "    id: Optional[str] = None\n" + res_fields
        else:
            res_fields = "    id: Optional[str] = None"

        req_schema_code = f"""
from pydantic import BaseModel

class {req_schema_name}(BaseModel):
{req_fields}
"""
        res_schema_code = f"""
from pydantic import BaseModel
from typing import Optional

class {res_schema_name}(BaseModel):
{res_fields}
"""
        (schemas_dir / f"{resource_snake}_request.py").write_text(req_schema_code.strip() + "\n", encoding="utf-8")
        (schemas_dir / f"{resource_snake}_response.py").write_text(res_schema_code.strip() + "\n", encoding="utf-8")

        # Controller
        controller_code = f"""
from dataclasses import asdict
from typing import Optional
from app.presentation.shared.http_response import HttpResponse
from app.presentation.v1.schemas.{resource_snake}_response import {res_schema_name}
from app.presentation.v1.schemas.{resource_snake}_request import {req_schema_name}
from app.application.{resource_snake}.mappers.{resource_snake}_mapper import {resource_pascal}Mapper
from app.application.{resource_snake}.dtos.{resource_snake}_dto import {resource_pascal}DTO
{"from app.application.%s.use_cases.list_%s import List%sUseCase" % (resource_snake, resource_snake, resource_pascal) if "GET" in meths else ""}
{"from app.application.%s.use_cases.get_%s import Get%sUseCase" % (resource_snake, resource_snake, resource_pascal) if "GET" in meths else ""}
{"from app.application.%s.use_cases.create_%s import Create%sUseCase" % (resource_snake, resource_snake, resource_pascal) if "POST" in meths else ""}
{"from app.application.%s.use_cases.update_%s import Update%sUseCase" % (resource_snake, resource_snake, resource_pascal) if "PUT" in meths else ""}
{"from app.application.%s.use_cases.delete_%s import Delete%sUseCase" % (resource_snake, resource_snake, resource_pascal) if "DELETE" in meths else ""}

class {resource_pascal}Controller:
    def __init__(self{", list_uc: List%sUseCase" % resource_pascal if "GET" in meths else ""}{", get_uc: Get%sUseCase" % resource_pascal if "GET" in meths else ""}{", create_uc: Create%sUseCase" % resource_pascal if "POST" in meths else ""}{", update_uc: Update%sUseCase" % resource_pascal if "PUT" in meths else ""}{", delete_uc: Delete%sUseCase" % resource_pascal if "DELETE" in meths else ""}) -> None:
{"        self._list_uc = list_uc" if "GET" in meths else ""}
{"        self._get_uc = get_uc" if "GET" in meths else ""}
{"        self._create_uc = create_uc" if "POST" in meths else ""}
{"        self._update_uc = update_uc" if "PUT" in meths else ""}
{"        self._delete_uc = delete_uc" if "DELETE" in meths else ""}

{"    def list(self) -> HttpResponse[list[%s]]:" % res_schema_name if "GET" in meths else ""}
{"        entities = self._list_uc.execute()" if "GET" in meths else ""}
{"        dtos = [ %sMapper.to_dto(e) for e in entities ]" % resource_pascal if "GET" in meths else ""}
{"        data = [ %s(**asdict(d)) for d in dtos ]" % res_schema_name if "GET" in meths else ""}
{"        return HttpResponse[list[%s]](success=True, data=data)" % res_schema_name if "GET" in meths else ""}

{"    def get(self, identifier: str) -> HttpResponse[%s]:" % res_schema_name if "GET" in meths else ""}
{"        entity = self._get_uc.execute(identifier)" if "GET" in meths else ""}
{"        dto = %sMapper.to_dto(entity) if entity else None" % resource_pascal if "GET" in meths else ""}
{"        data = %s(**asdict(dto)) if dto else None" % res_schema_name if "GET" in meths else ""}
{"        return HttpResponse[%s](success=True, data=data)" % res_schema_name if "GET" in meths else ""}

{"    def create(self, req: %s) -> HttpResponse[%s]:" % (req_schema_name, res_schema_name) if "POST" in meths else ""}
{"        dto = %sDTO(id=None, **req.model_dump())" % resource_pascal if "POST" in meths else ""}
{"        entity = %sMapper.to_domain(dto)" % resource_pascal if "POST" in meths else ""}
{"        created = self._create_uc.execute(entity)" if "POST" in meths else ""}
{"        out = %sMapper.to_dto(created)" % resource_pascal if "POST" in meths else ""}
{"        return HttpResponse[%s](success=True, data=%s(**asdict(out)))" % (res_schema_name, res_schema_name) if "POST" in meths else ""}

{"    def update(self, identifier: str, req: %s) -> HttpResponse[%s]:" % (req_schema_name, res_schema_name) if "PUT" in meths else ""}
{"        dto = %sDTO(**req.model_dump())" % resource_pascal if "PUT" in meths else ""}
{"        entity = %sMapper.to_domain(dto)" % resource_pascal if "PUT" in meths else ""}
{"        updated = self._update_uc.execute(identifier, entity)" if "PUT" in meths else ""}
{"        out = %sMapper.to_dto(updated)" % resource_pascal if "PUT" in meths else ""}
{"        return HttpResponse[%s](success=True, data=%s(**asdict(out)))" % (res_schema_name, res_schema_name) if "PUT" in meths else ""}

{"    def delete(self, identifier: str) -> HttpResponse[None]:" if "DELETE" in meths else ""}
{"        self._delete_uc.execute(identifier)" if "DELETE" in meths else ""}
{"        return HttpResponse[None](success=True, data=None)" if "DELETE" in meths else ""}
"""
        controller_path.write_text(controller_code.strip() + "\n", encoding="utf-8")

        # Endpoints
        import textwrap as _tw

        endpoints_imports = [
            "from fastapi import APIRouter, Path, Request",
            "from app.presentation.shared.http_response import HttpResponse",
            f"from app.presentation.v1.schemas.{resource_snake}_response import {res_schema_name}",
            f"from app.presentation.v1.schemas.{resource_snake}_request import {req_schema_name}",
            f"from app.presentation.v1.endpoints.{resource_snake}.controller import {resource_pascal}Controller",
            "from app.core.di.container import Container",
        ]
        if "GET" in meths:
            endpoints_imports.append(f"from app.application.{resource_snake}.use_cases.list_{resource_snake} import List{resource_pascal}UseCase")
            endpoints_imports.append(f"from app.application.{resource_snake}.use_cases.get_{resource_snake} import Get{resource_pascal}UseCase")
        if "POST" in meths:
            endpoints_imports.append(f"from app.application.{resource_snake}.use_cases.create_{resource_snake} import Create{resource_pascal}UseCase")
        if "PUT" in meths:
            endpoints_imports.append(f"from app.application.{resource_snake}.use_cases.update_{resource_snake} import Update{resource_pascal}UseCase")
        if "DELETE" in meths:
            endpoints_imports.append(f"from app.application.{resource_snake}.use_cases.delete_{resource_snake} import Delete{resource_pascal}UseCase")

        endpoints_header = "\n".join(endpoints_imports) + "\n\nrouter = APIRouter(tags=[\"" + resource_snake + "\"])\n"
        body = []

        if "GET" in meths:
            body.append(_tw.dedent(f"""
            @router.get("{endpoint_path}", response_model=HttpResponse[list[{res_schema_name}]], status_code=200, summary="List {resource_snake}")
            def list_{resource_snake}(request: Request):
                container: Container = request.app.state.container
                controller = {resource_pascal}Controller(
                    list_uc=container.{resource_snake}_list_uc(),
                    get_uc=container.{resource_snake}_get_uc(),
                    create_uc=container.{resource_snake}_create_uc(),
                    update_uc=container.{resource_snake}_update_uc(),
                    delete_uc=container.{resource_snake}_delete_uc()
                )
                return controller.list()
            """).strip())

            body.append(_tw.dedent(f"""
            @router.get("{endpoint_path}" + "/{{identifier}}", response_model=HttpResponse[{res_schema_name}], status_code=200, summary="Get {resource_snake}")
            def get_{resource_snake}(
                request: Request,
                identifier: str = Path(..., description="ID do recurso"),
            ):
                container: Container = request.app.state.container
                controller = {resource_pascal}Controller(
                    list_uc=container.{resource_snake}_list_uc(),
                    get_uc=container.{resource_snake}_get_uc(),
                    create_uc=container.{resource_snake}_create_uc(),
                    update_uc=container.{resource_snake}_update_uc(),
                    delete_uc=container.{resource_snake}_delete_uc()
                )
                return controller.get(identifier)
            """).strip())

        if "POST" in meths:
            body.append(_tw.dedent(f"""
            @router.post("{endpoint_path}", response_model=HttpResponse[{res_schema_name}], status_code=201, summary="Create {resource_snake}")
            def create_{resource_snake}(
                request: Request,
                req: {req_schema_name},
            ):
                container: Container = request.app.state.container
                controller = {resource_pascal}Controller(
                    list_uc=container.{resource_snake}_list_uc(),
                    get_uc=container.{resource_snake}_get_uc(),
                    create_uc=container.{resource_snake}_create_uc(),
                    update_uc=container.{resource_snake}_update_uc(),
                    delete_uc=container.{resource_snake}_delete_uc()
                )
                return controller.create(req)
            """).strip())

        if "PUT" in meths:
            body.append(_tw.dedent(f"""
            @router.put("{endpoint_path}" + "/{{identifier}}", response_model=HttpResponse[{res_schema_name}], status_code=200, summary="Update {resource_snake}")
            def update_{resource_snake}(
                request: Request,
                req: {req_schema_name},
                identifier: str = Path(..., description="ID do recurso"),
            ):
                container: Container = request.app.state.container
                controller = {resource_pascal}Controller(
                    list_uc=container.{resource_snake}_list_uc(),
                    get_uc=container.{resource_snake}_get_uc(),
                    create_uc=container.{resource_snake}_create_uc(),
                    update_uc=container.{resource_snake}_update_uc(),
                    delete_uc=container.{resource_snake}_delete_uc()
                )
                return controller.update(identifier, req)
            """).strip())

        if "DELETE" in meths:
            body.append(_tw.dedent(f"""
            @router.delete("{endpoint_path}" + "/{{identifier}}", status_code=204, summary="Delete {resource_snake}")
            def delete_{resource_snake}(
                request: Request,
                identifier: str = Path(..., description="ID do recurso"),
            ):
                container: Container = request.app.state.container
                controller = {resource_pascal}Controller(
                    list_uc=container.{resource_snake}_list_uc(),
                    get_uc=container.{resource_snake}_get_uc(),
                    create_uc=container.{resource_snake}_create_uc(),
                    update_uc=container.{resource_snake}_update_uc(),
                    delete_uc=container.{resource_snake}_delete_uc()
                )
                return controller.delete(identifier)
            """).strip())

        endpoints_path.write_text((endpoints_header + "\n\n".join(body) + "\n"), encoding="utf-8")

        # --- DI Container wiring ---
        container_path = APP_ROOT / "app" / "core" / "di" / "container.py"

        import_lines = []
        import_lines.append(f"from app.infrastructure.{resource_snake}.adapters.in_memory_{resource_snake}_adapter import InMemory{resource_pascal}Adapter")
        if "GET" in meths:
            import_lines.append(f"from app.application.{resource_snake}.use_cases.list_{resource_snake} import List{resource_pascal}UseCase")
            import_lines.append(f"from app.application.{resource_snake}.use_cases.get_{resource_snake} import Get{resource_pascal}UseCase")
        if "POST" in meths:
            import_lines.append(f"from app.application.{resource_snake}.use_cases.create_{resource_snake} import Create{resource_pascal}UseCase")
        if "PUT" in meths:
            import_lines.append(f"from app.application.{resource_snake}.use_cases.update_{resource_snake} import Update{resource_pascal}UseCase")
        if "DELETE" in meths:
            import_lines.append(f"from app.application.{resource_snake}.use_cases.delete_{resource_snake} import Delete{resource_pascal}UseCase")
        import_block = "\n".join(import_lines)

        provider_lines = []
        provider_lines.append(f"    # {resource_pascal} providers")
        provider_lines.append(f"    {resource_snake}_adapter = providers.Singleton(InMemory{resource_pascal}Adapter)")
        if "GET" in meths:
            provider_lines.append(f"    {resource_snake}_list_uc = providers.Singleton(List{resource_pascal}UseCase, port={resource_snake}_adapter)")
            provider_lines.append(f"    {resource_snake}_get_uc = providers.Singleton(Get{resource_pascal}UseCase, port={resource_snake}_adapter)")
        if "POST" in meths:
            provider_lines.append(f"    {resource_snake}_create_uc = providers.Singleton(Create{resource_pascal}UseCase, port={resource_snake}_adapter)")
        if "PUT" in meths:
            provider_lines.append(f"    {resource_snake}_update_uc = providers.Singleton(Update{resource_pascal}UseCase, port={resource_snake}_adapter)")
        if "DELETE" in meths:
            provider_lines.append(f"    {resource_snake}_delete_uc = providers.Singleton(Delete{resource_pascal}UseCase, port={resource_snake}_adapter)")
        providers_block = "\n".join(provider_lines)

        insert_in_container(container_path, f"InMemory{resource_pascal}Adapter", import_block, providers_block)

        # --- API Router registration ---
        api_router_path = APP_ROOT / "app" / "presentation" / "v1" / "api.py"
        api_text = api_router_path.read_text(encoding="utf-8")

        import_router_line = f"from app.presentation.v1.endpoints.{resource_snake}.endpoints import router as {resource_snake}_router"
        if import_router_line not in api_text:
            api_text = import_router_line + "\n" + api_text

        include_line = f"api_router.include_router({resource_snake}_router)"
        if include_line not in api_text:
            if "api_router = APIRouter(" not in api_text:
                api_text = "from fastapi import APIRouter\n\napi_router = APIRouter(prefix=\"/api/v1\")\n" + api_text
            api_text += f"\n{include_line}\n"

        api_router_path.write_text(api_text, encoding="utf-8")

    typer.secho(f"Recurso '{resource_snake}' gerado com sucesso!", fg=typer.colors.GREEN)
    typer.echo(f"- Endpoint base: {endpoint_path}")
    typer.echo(f"- Métodos: {', '.join(meths)}")
    typer.echo(f"- Entidade: app/domain/{resource_snake}/entities/{resource_snake}.py")
    typer.echo(f"- Controller & Endpoints: app/presentation/v1/endpoints/{resource_snake}/")
    typer.echo(f"- DI: app/core/di/container.py atualizado")
    typer.echo(f"- Router: app/presentation/v1/api.py atualizado")
    typer.echo("Dica: rode a API e teste o novo endpoint.")


if __name__ == "__main__":
    app()
