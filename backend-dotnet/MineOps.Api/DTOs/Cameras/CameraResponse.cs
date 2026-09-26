using MineOps.Api.Models;

namespace MineOps.Api.DTOs.Cameras;

public record CameraResponse(
    Guid Id,
    string Name,
    string? Location,
    string StreamUrl,
    CameraStatus Status,
    string? Description,
    DateTimeOffset CreatedAtUtc,
    DateTimeOffset? UpdatedAtUtc);

