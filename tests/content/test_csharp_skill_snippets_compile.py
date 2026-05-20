"""T178 (commit 26, C-Q1-Q5): C# skill snippets must compile.

Per Codex round-3 R5: write a temporary `net8.0` SDK project with
`FrameworkReference Include="Microsoft.AspNetCore.App"`, stub
MediatR/FluentValidation/Grpc.Core types locally (no NuGet / no network),
include the FIXED versions of:
- controller skill `Problem(detail:, statusCode:)` (post-C-Q4)
- minimal-api filter `ValidateAsync(x, ct)` (post-C-Q2)
- gRPC service method `Send(cmd, context.CancellationToken)` (post-C-Q1)

Then run `dotnet build --nologo` and assert exit 0.

If `dotnet` is missing on PATH (developer machine, ephemeral sandbox),
the test is skipped — the CI smoke job runs on hosts with the SDK
installed and exercises this gate per the smoke matrix.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

SDK_PROJECT_NAME = "csq_compile_scaffold"


CSPROJ = """<Project Sdk="Microsoft.NET.Sdk.Web">
  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
    <Nullable>enable</Nullable>
    <ImplicitUsings>enable</ImplicitUsings>
    <LangVersion>latest</LangVersion>
    <OutputType>Library</OutputType>
    <NoWarn>$(NoWarn);CS1591;CS0436;CS8019;CS8632</NoWarn>
  </PropertyGroup>
</Project>
"""


# Minimal stubs for MediatR, FluentValidation, Grpc.Core so the snippets
# below compile without any NuGet restore. Each interface mirrors the
# real one closely enough for the snippets to type-check.
STUBS = """
using System;
using System.Threading;
using System.Threading.Tasks;
using System.Collections.Generic;

namespace MediatR
{
    public interface IRequest<T> { }

    public interface IMediator
    {
        Task<T> Send<T>(IRequest<T> request, CancellationToken ct = default);
    }
}

namespace FluentValidation
{
    public interface IValidator<T>
    {
        Task<ValidationResult> ValidateAsync(T instance, CancellationToken ct = default);
    }

    public class ValidationResult
    {
        public bool IsValid => true;
        public IDictionary<string, string[]> ToDictionary() => new Dictionary<string, string[]>();
    }
}

namespace Grpc.Core
{
    public class ServerCallContext
    {
        public CancellationToken CancellationToken => CancellationToken.None;
    }
}
"""


# C-Q4 fixed snippet: controller uses Problem(detail:, statusCode:) named args.
CONTROLLER_SNIPPET = """
using System.Threading;
using System.Threading.Tasks;
using MediatR;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;

namespace Acme.Sales.Api.Controllers
{
    public record Result<T>(bool IsSuccess, T? Value, string? Error)
    {
        public static Result<T> Ok(T value) => new(true, value, null);
        public static Result<T> Fail(string err) => new(false, default, err);
    }

    public record GetOrdersQuery(int page, int pageSize, string? search) : IRequest<Result<string>>;

    [ApiController]
    [Route("api/orders")]
    public class OrdersController : ControllerBase
    {
        private readonly IMediator Mediator;
        public OrdersController(IMediator m) { Mediator = m; }

        [HttpGet]
        public async Task<IActionResult> Get(
            int page = 1, int pageSize = 50, string? search = null,
            CancellationToken ct = default)
        {
            var query = new GetOrdersQuery(page, pageSize, search);
            var result = await Mediator.Send(query, ct);
            return result.IsSuccess
                ? Ok(result.Value)
                : Problem(detail: result.Error, statusCode: StatusCodes.Status400BadRequest);
        }
    }
}
"""


# C-Q2 fixed snippet: minimal-api filter ValidateAsync(x, ct).
MINIMAL_API_SNIPPET = """
using System.Linq;
using System.Threading.Tasks;
using FluentValidation;
using Microsoft.AspNetCore.Http;

namespace Acme.Sales.Api.Filters
{
    public class ValidationFilter<TRequest> : IEndpointFilter
    {
        private readonly IValidator<TRequest> validator;
        public ValidationFilter(IValidator<TRequest> v) { validator = v; }

        public async ValueTask<object?> InvokeAsync(
            EndpointFilterInvocationContext context, EndpointFilterDelegate next)
        {
            var request = context.Arguments.OfType<TRequest>().FirstOrDefault();
            if (request is null)
                return Results.BadRequest("Request body is required");

            var result = await validator.ValidateAsync(
                request, context.HttpContext.RequestAborted);
            if (!result.IsValid)
                return Results.ValidationProblem(result.ToDictionary());

            return await next(context);
        }
    }
}
"""


# C-Q1 fixed snippet: gRPC service forwards context.CancellationToken.
GRPC_SNIPPET = """
using System.Threading.Tasks;
using Grpc.Core;
using MediatR;

namespace Acme.Sales.Grpc.Services
{
    public record CreateOrderCommand(string Customer) : IRequest<string>;
    public class CreateOrderResponse { public string OrderId { get; set; } = ""; }

    public class OrderCommandsService
    {
        private readonly IMediator mediator;
        public OrderCommandsService(IMediator m) { mediator = m; }

        public async Task<CreateOrderResponse> CreateOrder(
            CreateOrderCommand request, ServerCallContext context)
        {
            // C-Q1: forward the cancellation token
            var output = await mediator.Send(request, context.CancellationToken);
            return new CreateOrderResponse { OrderId = output };
        }
    }
}
"""


def _have_dotnet_sdk() -> bool:
    return shutil.which("dotnet") is not None


@pytest.mark.skipif(not _have_dotnet_sdk(), reason="dotnet SDK not on PATH")
def test_csharp_skill_snippets_compile(tmp_path: Path) -> None:
    """The C-Q1/C-Q2/C-Q4 fixed snippets must compile against net8.0."""
    proj = tmp_path / SDK_PROJECT_NAME
    proj.mkdir()
    (proj / f"{SDK_PROJECT_NAME}.csproj").write_text(CSPROJ, encoding="utf-8")
    (proj / "Stubs.cs").write_text(STUBS, encoding="utf-8")
    (proj / "Controller.cs").write_text(CONTROLLER_SNIPPET, encoding="utf-8")
    (proj / "MinimalApi.cs").write_text(MINIMAL_API_SNIPPET, encoding="utf-8")
    (proj / "Grpc.cs").write_text(GRPC_SNIPPET, encoding="utf-8")

    result = subprocess.run(
        ["dotnet", "build", "--nologo", "-warnaserror:false"],
        cwd=proj,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"C# skill snippets failed to compile.\n"
        f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
    )
