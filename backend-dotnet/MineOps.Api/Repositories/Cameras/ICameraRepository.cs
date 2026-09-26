using MineOps.Api.Models;

namespace MineOps.Api.Repositories.Cameras;

public interface ICameraRepository
{

    Task<Camera> CreateAsync (Camera camera, CancellationToken cancellationToken);

    Task<(IReadOnlyList<Camera> Items, int TotalCount)> GetAllAsync(
        int page,
        int pageSize,
        CancellationToken cancellationToken = default);

    Task<Camera?> GetByIdAsync(
        Guid id,
        CancellationToken cancellationToken = default);

    //Task<(IReadOnlyList<Camera> Items, int TotalCount)> SearchAsync(
    //    string? search,
    //    CameraStatus? status,
    //    int page,
    //    int pageSize,
    //    CancellationToken cancellationToken = default);

    //Task<Camera> CreateAsync(
    //    Camera camera,
    //    CancellationToken cancellationToken = default);

    //Task<bool> UpdateAsync(
    //    Camera camera,
    //    CancellationToken cancellationToken = default);

    //Task<bool> DeleteAsync(
    //    Guid id,
    //    CancellationToken cancellationToken = default);
}