FROM mcr.microsoft.com/dotnet/aspnet:{{ dotnet_version }} AS base
WORKDIR /app

FROM mcr.microsoft.com/dotnet/sdk:{{ dotnet_version }} AS build
WORKDIR /src
COPY ["src/{{ Company }}.{{ Domain }}.Processor.Host/{{ Company }}.{{ Domain }}.Processor.Host.csproj", "src/{{ Company }}.{{ Domain }}.Processor.Host/"]
COPY ["src/{{ Company }}.{{ Domain }}.Processor.Application/{{ Company }}.{{ Domain }}.Processor.Application.csproj", "src/{{ Company }}.{{ Domain }}.Processor.Application/"]
COPY ["src/{{ Company }}.{{ Domain }}.Processor.Domain/{{ Company }}.{{ Domain }}.Processor.Domain.csproj", "src/{{ Company }}.{{ Domain }}.Processor.Domain/"]
COPY ["src/{{ Company }}.{{ Domain }}.Processor.Infra/{{ Company }}.{{ Domain }}.Processor.Infra.csproj", "src/{{ Company }}.{{ Domain }}.Processor.Infra/"]
RUN dotnet restore "src/{{ Company }}.{{ Domain }}.Processor.Host/{{ Company }}.{{ Domain }}.Processor.Host.csproj"
COPY . .
RUN dotnet publish "src/{{ Company }}.{{ Domain }}.Processor.Host/{{ Company }}.{{ Domain }}.Processor.Host.csproj" -c Release -o /app/publish

FROM base AS final
WORKDIR /app
COPY --from=build /app/publish .
USER $APP_UID
ENTRYPOINT ["dotnet", "{{ Company }}.{{ Domain }}.Processor.Host.dll"]
