using System.Globalization;
using Grpc.Core;
using Grpc.Core.Interceptors;

namespace {{ Company }}.{{ Domain }}.Queries.Grpc.Interceptors;

public class ThreadCultureInterceptor : Interceptor
{
    public override async Task<TResponse> UnaryServerHandler<TRequest, TResponse>(
        TRequest request,
        ServerCallContext context,
        UnaryServerMethod<TRequest, TResponse> continuation)
    {
        var language = context.RequestHeaders.GetValue("language");
        if (!string.IsNullOrEmpty(language))
        {
            var culture = new CultureInfo(language);
            Thread.CurrentThread.CurrentCulture = culture;
            Thread.CurrentThread.CurrentUICulture = culture;
        }

        return await continuation(request, context);
    }
}
