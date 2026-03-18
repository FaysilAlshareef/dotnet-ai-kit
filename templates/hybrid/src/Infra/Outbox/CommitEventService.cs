using {{ Company }}.{{ Domain }}.Commands.Application.Contracts.Repositories;
using {{ Company }}.{{ Domain }}.Commands.Application.Contracts.Services.BaseServices;
using {{ Company }}.{{ Domain }}.Commands.Application.Contracts.Services.ServiceBus;
using {{ Company }}.{{ Domain }}.Commands.Domain.Core;
using {{ Company }}.{{ Domain }}.Commands.Domain.Entities;
using {{ Company }}.{{ Domain }}.Commands.Domain.Events;

namespace {{ Company }}.{{ Domain }}.Commands.Infra.Services.BaseService;

public class CommitEventService(IUnitOfWork unitOfWork, IServiceBusPublisher serviceBusPublisher)
    : ICommitEventService
{
    private readonly IUnitOfWork _unitOfWork = unitOfWork;
    private readonly IServiceBusPublisher _serviceBusPublisher = serviceBusPublisher;

    public async Task CommitNewEventsAsync<T>(Aggregate<T> model)
    {
        var newEvents = model.GetUncommittedEvents();

        await SaveToDatabase(newEvents);

        model.MarkChangesAsCommitted();

        _serviceBusPublisher.StartPublish();
    }

    private async Task SaveToDatabase(IReadOnlyList<Event> newEvents)
    {
        await _unitOfWork.Events.AddRangeAsync(newEvents);

        var messages = OutboxMessage.ToManyMessages(newEvents);

        await _unitOfWork.OutboxMessages.AddRangeAsync(messages);

        await _unitOfWork.SaveChangesAsync();
    }
}
