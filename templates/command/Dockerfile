FROM mcr.microsoft.com/dotnet/aspnet:{{ dotnet_version }} AS base
WORKDIR /app
EXPOSE 8080

FROM mcr.microsoft.com/dotnet/sdk:{{ dotnet_version }} AS build
WORKDIR /src
COPY ["src/{{ Company }}.{{ Domain }}.Commands.Grpc/{{ Company }}.{{ Domain }}.Commands.Grpc.csproj", "src/{{ Company }}.{{ Domain }}.Commands.Grpc/"]
COPY ["src/{{ Company }}.{{ Domain }}.Commands.Application/{{ Company }}.{{ Domain }}.Commands.Application.csproj", "src/{{ Company }}.{{ Domain }}.Commands.Application/"]
COPY ["src/{{ Company }}.{{ Domain }}.Commands.Domain/{{ Company }}.{{ Domain }}.Commands.Domain.csproj", "src/{{ Company }}.{{ Domain }}.Commands.Domain/"]
COPY ["src/{{ Company }}.{{ Domain }}.Commands.Infra/{{ Company }}.{{ Domain }}.Commands.Infra.csproj", "src/{{ Company }}.{{ Domain }}.Commands.Infra/"]
RUN dotnet restore "src/{{ Company }}.{{ Domain }}.Commands.Grpc/{{ Company }}.{{ Domain }}.Commands.Grpc.csproj"
COPY . .
RUN dotnet publish "src/{{ Company }}.{{ Domain }}.Commands.Grpc/{{ Company }}.{{ Domain }}.Commands.Grpc.csproj" -c Release -o /app/publish

FROM base AS final
WORKDIR /app
COPY --from=build /app/publish .
USER $APP_UID
ENTRYPOINT ["dotnet", "{{ Company }}.{{ Domain }}.Commands.Grpc.dll"]
