using Grpc.Core;
using Grpc.Core.Interceptors;

namespace {{ Company }}.{{ Domain }}.Commands.Grpc.Interceptors;

/// <summary>
/// Catches domain exceptions and converts to RpcException with appropriate StatusCode.
/// Maps: NotFound -> NotFound, Validation -> InvalidArgument, Business -> FailedPrecondition.
/// </summary>
public class ApplicationExceptionInterceptor : Interceptor
{
    public override async Task<TResponse> UnaryServerHandler<TRequest, TResponse>(
        TRequest request,
        ServerCallContext context,
        UnaryServerMethod<TRequest, TResponse> continuation)
    {
        try
        {
            return await continuation(request, context);
        }
        catch (KeyNotFoundException ex)
        {
            throw new RpcException(new Status(StatusCode.NotFound, ex.Message));
        }
        catch (ArgumentException ex)
        {
            throw new RpcException(new Status(StatusCode.InvalidArgument, ex.Message));
        }
        catch (InvalidOperationException ex)
        {
            throw new RpcException(new Status(StatusCode.FailedPrecondition, ex.Message));
        }
    }
}
