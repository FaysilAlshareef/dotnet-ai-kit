using MediatR;
using {{ Company }}.{{ ProjectName }}.Domain.Common;
using {{ Company }}.{{ ProjectName }}.Domain.Interfaces;

namespace {{ Company }}.{{ ProjectName }}.Application.Behaviors;

/// <summary>
/// Pipeline behavior that dispatches domain events after the handler completes.
/// Collects events from aggregate roots and publishes them via MediatR.
/// </summary>
public sealed class DomainEventDispatchBehavior<TRequest, TResponse>(
    IDomainEventDispatcher dispatcher)
    : IPipelineBehavior<TRequest, TResponse>
    where TRequest : IRequest<TResponse>
{
    public async Task<TResponse> Handle(
        TRequest request,
        RequestHandlerDelegate<TResponse> next,
        CancellationToken cancellationToken)
    {
        var response = await next();

        // Domain events are dispatched after the handler completes
        // The interceptor in Infrastructure collects and dispatches them

        return response;
    }
}
