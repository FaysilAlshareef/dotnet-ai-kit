using System.Net.Http.Json;

namespace {{ Company }}.ControlPanel.{{ Domain }}.Gateways;

public abstract record ResponseResult<T>;
public sealed record SuccessResult<T>(T Value) : ResponseResult<T>;
public sealed record FailedResult<T>(ProblemDetails ProblemDetails) : ResponseResult<T>;

public sealed record ProblemDetails
{
    public string? Title { get; init; }
    public string? Detail { get; init; }
    public int Status { get; init; }
}

public static class HttpExtensions
{
    public static async Task<ResponseResult<T>> GetAsync<T>(
        this HttpClient client, string url)
    {
        var response = await client.GetAsync(url);
        if (response.IsSuccessStatusCode)
        {
            var result = await response.Content.ReadFromJsonAsync<T>();
            return new SuccessResult<T>(result!);
        }

        var problem = await response.Content.ReadFromJsonAsync<ProblemDetails>()
            ?? new ProblemDetails { Title = "Error", Detail = response.ReasonPhrase, Status = (int)response.StatusCode };
        return new FailedResult<T>(problem);
    }

    public static async Task<ResponseResult<T>> PostAsync<T>(
        this HttpClient client, string url, object body)
    {
        var response = await client.PostAsJsonAsync(url, body);
        if (response.IsSuccessStatusCode)
        {
            var result = await response.Content.ReadFromJsonAsync<T>();
            return new SuccessResult<T>(result!);
        }

        var problem = await response.Content.ReadFromJsonAsync<ProblemDetails>()
            ?? new ProblemDetails { Title = "Error", Detail = response.ReasonPhrase, Status = (int)response.StatusCode };
        return new FailedResult<T>(problem);
    }

    public static void Switch<T>(this ResponseResult<T> result,
        Action<SuccessResult<T>> onSuccess,
        Action<FailedResult<T>> onFailure)
    {
        switch (result)
        {
            case SuccessResult<T> success:
                onSuccess(success);
                break;
            case FailedResult<T> failure:
                onFailure(failure);
                break;
        }
    }
}
