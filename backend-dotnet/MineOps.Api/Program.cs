using Microsoft.EntityFrameworkCore;
using MineOps.Api.Data;
using MineOps.Api.Repositories.Cameras;
using System.Text.Json.Serialization;

var builder = WebApplication.CreateBuilder(args);

// dbContext configuration
var connectionString =
    builder.Configuration.GetConnectionString("MineOpsDb")
    ?? throw new InvalidOperationException(
        "Connection string 'MineOpsDb' was not found.");

builder.Services.AddDbContext<MineOpsDbContext>(options =>
    options.UseNpgsql(connectionString));

// Add services to the container.
builder.Services.AddScoped<ICameraRepository, CameraRepository>();


builder.Services
    .AddControllers()
    .AddJsonOptions(options =>
    {
        options.JsonSerializerOptions.Converters.Add(
            new JsonStringEnumConverter());
    });
// Learn more about configuring OpenAPI at https://aka.ms/aspnet/openapi
builder.Services.AddOpenApi();

var app = builder.Build();

// Configure the HTTP request pipeline.
if (app.Environment.IsDevelopment())
{
    app.MapOpenApi();

    app.UseSwaggerUI(options =>
    {
        options.SwaggerEndpoint(
            "/openapi/v1.json",
            "MineOps API v1");
    });
}

app.UseHttpsRedirection();

app.UseAuthorization();

app.MapControllers();

app.Run();
