FROM mcr.microsoft.com/dotnet/aspnet:{{ dotnet_version }} AS base
WORKDIR /app
EXPOSE 8080

FROM mcr.microsoft.com/dotnet/sdk:{{ dotnet_version }} AS build
WORKDIR /src
COPY ["src/{{ Company }}.{{ Domain }}.Queries.Grpc/{{ Company }}.{{ Domain }}.Queries.Grpc.csproj", "src/{{ Company }}.{{ Domain }}.Queries.Grpc/"]
COPY ["src/{{ Company }}.{{ Domain }}.Queries.Application/{{ Company }}.{{ Domain }}.Queries.Application.csproj", "src/{{ Company }}.{{ Domain }}.Queries.Application/"]
COPY ["src/{{ Company }}.{{ Domain }}.Queries.Domain/{{ Company }}.{{ Domain }}.Queries.Domain.csproj", "src/{{ Company }}.{{ Domain }}.Queries.Domain/"]
COPY ["src/{{ Company }}.{{ Domain }}.Queries.Infra/{{ Company }}.{{ Domain }}.Queries.Infra.csproj", "src/{{ Company }}.{{ Domain }}.Queries.Infra/"]
RUN dotnet restore "src/{{ Company }}.{{ Domain }}.Queries.Grpc/{{ Company }}.{{ Domain }}.Queries.Grpc.csproj"
COPY . .
RUN dotnet publish "src/{{ Company }}.{{ Domain }}.Queries.Grpc/{{ Company }}.{{ Domain }}.Queries.Grpc.csproj" -c Release -o /app/publish

FROM base AS final
WORKDIR /app
COPY --from=build /app/publish .
USER $APP_UID
ENTRYPOINT ["dotnet", "{{ Company }}.{{ Domain }}.Queries.Grpc.dll"]
