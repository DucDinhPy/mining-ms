using MineOps.Api.DTOs.Cameras;
using MineOps.Api.Models;

namespace MineOps.Api.Mappings.Cameras;

public static class CameraMapper
{
    public static CameraResponse ToResponse(this Camera camera)
    {
        return new CameraResponse(
            camera.Id,
            camera.Name,
            camera.Location,
            camera.StreamUrl,
            camera.Status,
            camera.Description,
            camera.CreatedAtUtc,
            camera.UpdatedAtUtc);
    }
}