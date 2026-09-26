namespace MineOps.Api.Models;

public class Camera
{
    public Guid Id { get; set; } = Guid.NewGuid();

    public string Name { get; set; } = string.Empty;

    public string Location { get; set; } = string.Empty;

    public string StreamUrl { get; set; } = string.Empty;

    public CameraStatus Status { get; set; } = CameraStatus.Offline;

    public string? Description { get; set; }

    public DateTimeOffset CreatedAtUtc { get; set; } = DateTimeOffset.UtcNow;

    public DateTimeOffset? UpdatedAtUtc { get; set; }
}