using {{ Company }}.{{ Domain }}.Commands.Application.Contracts.Repositories;
using {{ Company }}.{{ Domain }}.Commands.Application.Contracts.Services.ServiceBus;
using {{ Company }}.{{ Domain }}.Commands.Domain.Entities;
using {{ Company }}.{{ Domain }}.Commands.Domain.Events;
using Azure.Messaging.ServiceBus;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Newtonsoft.Json;
using System.Text;

namespace {{ Company }}.{{ Domain }}.Commands.Infra.Services.ServiceBus;

public class ServiceBusPublisher : IServiceBusPublisher
{
    private readonly IServiceProvider _serviceProvider;
    private readonly ServiceBusSender _sender;
    private readonly ILogger<ServiceBusPublisher> _logger;

    private static readonly object _lockObject = new();
    private int lockedScopes;

    public ServiceBusPublisher(
        IServiceProvider serviceProvider,
        IConfiguration configuration,
        ServiceBusClient serviceBusClient,
        ILogger<ServiceBusPublisher> logger)
    {
        _serviceProvider = serviceProvider;
        _sender = serviceBusClient.CreateSender(configuration["ServiceBus:Topic"]);
        _logger = logger;
    }

    public void StartPublish()
    {
        // Don't wait.
        Task.Run(PublishNonPublishedMessages);
    }

    private void PublishNonPublishedMessages()
    {
        _logger.LogInformation("Publishing to service bus requested.");

        if (lockedScopes > 2)
            return;

        lockedScopes++;

        _logger.LogWarning(
            "Thread attempting to lock a scope in publisher with locked scopes = {LockedScopes}",
            lockedScopes);

        try
        {
            lock (_lockObject)
            {
                using var scope = _serviceProvider.CreateScope();

                var unitOfWork = scope.ServiceProvider.GetRequiredService<IUnitOfWork>();

                while (unitOfWork.OutboxMessages.AnyAsync().GetAwaiter().GetResult())
                {
                    var messages = unitOfWork.OutboxMessages
                        .GeOutboxMessageAsync(200).GetAwaiter().GetResult();

                    _logger.LogInformation("Fetched Message From outbox {Count}", messages.Count);

                    PublishAndRemoveMessagesAsync(messages, unitOfWork).GetAwaiter().GetResult();
                }
            }
        }
        catch (Exception e)
        {
            _logger.LogCritical(e, "Message published failed while attempting to send messages");
        }
        finally
        {
            lockedScopes--;
            _logger.LogWarning(
                "Thread let go of the lock in publisher with locked scopes = {LockedScopes}",
                lockedScopes);
        }
    }

    private async Task PublishAndRemoveMessagesAsync(
        IEnumerable<OutboxMessage> messages, IUnitOfWork unitOfWork)
    {
        foreach (var message in messages)
        {
            await SendMessageAsync(message.Event!);

            await unitOfWork.OutboxMessages.RemoveAsync(message);

            await unitOfWork.SaveChangesAsync();
        }

        await Task.CompletedTask;
    }

    private async Task SendMessageAsync(Event @event)
    {
        var body = new MessageBody()
        {
            AggregateId = @event.AggregateId,
            DateTime = @event.DateTime,
            Sequence = @event.Sequence,
            Type = @event.Type.ToString(),
            UserId = @event.UserId?.ToString(),
            Version = @event.Version,
            Data = ((dynamic)@event).Data
        };

        var messageBody = JsonConvert.SerializeObject(body);

        var message = new ServiceBusMessage(Encoding.UTF8.GetBytes(messageBody))
        {
            CorrelationId = @event.Id.ToString(),
            MessageId = @event.Id.ToString(),
            PartitionKey = @event.AggregateId.ToString(),
            SessionId = @event.AggregateId.ToString(),
            Subject = @event.Type.ToString(),
            ApplicationProperties =
            {
                { nameof(@event.AggregateId), @event.AggregateId },
                { nameof(@event.Sequence), @event.Sequence },
                { nameof(@event.Version), @event.Version },
            }
        };

        await _sender.SendMessageAsync(message);
    }
}

public class MessageBody
{
    public Guid AggregateId { get; set; }
    public int Sequence { get; set; }
    public string? UserId { get; set; }
    public required string Type { get; set; }
    public required object Data { get; set; }
    public DateTime DateTime { get; set; }
    public int Version { get; set; }
}
