FROM mcr.microsoft.com/dotnet/aspnet:{{ dotnet_version }} AS base
WORKDIR /app
EXPOSE 8080

FROM mcr.microsoft.com/dotnet/sdk:{{ dotnet_version }} AS build
WORKDIR /src
COPY ["src/{{ Company }}.Gateways.{{ Domain }}.Management/{{ Company }}.Gateways.{{ Domain }}.Management.csproj", "src/{{ Company }}.Gateways.{{ Domain }}.Management/"]
RUN dotnet restore "src/{{ Company }}.Gateways.{{ Domain }}.Management/{{ Company }}.Gateways.{{ Domain }}.Management.csproj"
COPY . .
RUN dotnet publish "src/{{ Company }}.Gateways.{{ Domain }}.Management/{{ Company }}.Gateways.{{ Domain }}.Management.csproj" -c Release -o /app/publish

FROM base AS final
WORKDIR /app
COPY --from=build /app/publish .
USER $APP_UID
ENTRYPOINT ["dotnet", "{{ Company }}.Gateways.{{ Domain }}.Management.dll"]
