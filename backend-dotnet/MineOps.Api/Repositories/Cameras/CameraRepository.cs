using Microsoft.EntityFrameworkCore;
using MineOps.Api.Data;
using MineOps.Api.Models;

namespace MineOps.Api.Repositories.Cameras;

public class CameraRepository : ICameraRepository
{
    private readonly MineOpsDbContext _dbContext;

    public CameraRepository(MineOpsDbContext dbContext)
    {
        _dbContext = dbContext;
    }

    public async Task<Camera> CreateAsync(
        Camera camera,
        CancellationToken cancellationToken)
    {
        camera.Id = Guid.NewGuid();
        camera.CreatedAtUtc = DateTimeOffset.UtcNow;
        camera.UpdatedAtUtc = null;
        await _dbContext.Cameras.AddAsync(camera, cancellationToken);
        await _dbContext.SaveChangesAsync(cancellationToken);
        return camera;
    }

    public async Task<Camera?> GetByIdAsync(
    Guid id,
    CancellationToken cancellationToken = default)
    {
        return await _dbContext.Cameras
            .AsNoTracking()
            .FirstOrDefaultAsync(
                camera => camera.Id == id,
                cancellationToken);
    }

    public async Task<(IReadOnlyList<Camera> Items, int TotalCount)> GetAllAsync(
        int page,
        int pageSize,
        CancellationToken cancellationToken = default)
    {
        page = Math.Max(page, 1);
        pageSize = Math.Clamp(pageSize, 1, 100);
        var query = _dbContext.Cameras
            .AsNoTracking()
            .AsQueryable();
        var totalCount = await query.CountAsync(cancellationToken);
        var items = await query
            .OrderBy(camera => camera.Name)
            .Skip((page - 1) * pageSize)
            .Take(pageSize)
            .ToListAsync(cancellationToken);
        return (items, totalCount);
    }


    //public async Task<IReadOnlyList<Camera>> ListCamerasAsync(
    //    CancellationToken cancellationToken = default)
    //{
    //    return await _dbContext.Cameras
    //        .AsNoTracking()
    //        .ToListAsync(cancellationToken);
    //}


    //public async Task<(IReadOnlyList<Camera> Items, int TotalCount)> SearchAsync(
    //    string? search,
    //    CameraStatus? status,
    //    int page,
    //    int pageSize,
    //    CancellationToken cancellationToken = default)
    //{
    //    page = Math.Max(page, 1);
    //    pageSize = Math.Clamp(pageSize, 1, 100);

    //    var query = _dbContext.Cameras
    //        .AsNoTracking()
    //        .AsQueryable();

    //    if (!string.IsNullOrWhiteSpace(search))
    //    {
    //        var searchTerm = search.Trim();

    //        query = query.Where(camera =>
    //            EF.Functions.ILike(
    //                camera.Name,
    //                $"%{searchTerm}%") ||
    //            (camera.Location != null &&
    //             EF.Functions.ILike(
    //                 camera.Location,
    //                 $"%{searchTerm}%")));
    //    }

    //    if (status.HasValue)
    //    {
    //        query = query.Where(
    //            camera => camera.Status == status.Value);
    //    }

    //    var totalCount = await query.CountAsync(cancellationToken);

    //    var items = await query
    //        .OrderBy(camera => camera.Name)
    //        .Skip((page - 1) * pageSize)
    //        .Take(pageSize)
    //        .ToListAsync(cancellationToken);

    //    return (items, totalCount);
    //}

    //public async Task<Camera> CreateAsync(
    //    Camera camera,
    //    CancellationToken cancellationToken = default)
    //{
    //    camera.Id = Guid.NewGuid();
    //    camera.CreatedAtUtc = DateTimeOffset.UtcNow;
    //    camera.UpdatedAtUtc = null;

    //    await _dbContext.Cameras.AddAsync(
    //        camera,
    //        cancellationToken);

    //    await _dbContext.SaveChangesAsync(cancellationToken);

    //    return camera;
    //}

    //public async Task<bool> UpdateAsync(
    //    Camera camera,
    //    CancellationToken cancellationToken = default)
    //{
    //    var existingCamera =
    //        await _dbContext.Cameras.FirstOrDefaultAsync(
    //            existing => existing.Id == camera.Id,
    //            cancellationToken);

    //    if (existingCamera is null)
    //    {
    //        return false;
    //    }

    //    existingCamera.Name = camera.Name;
    //    existingCamera.Location = camera.Location;
    //    existingCamera.StreamUrl = camera.StreamUrl;
    //    existingCamera.Status = camera.Status;
    //    existingCamera.Description = camera.Description;
    //    existingCamera.UpdatedAtUtc = DateTimeOffset.UtcNow;

    //    await _dbContext.SaveChangesAsync(cancellationToken);

    //    return true;
    //}

    //public async Task<bool> DeleteAsync(
    //    Guid id,
    //    CancellationToken cancellationToken = default)
    //{
    //    var camera = await _dbContext.Cameras.FindAsync(
    //        [id],
    //        cancellationToken);

    //    if (camera is null)
    //    {
    //        return false;
    //    }

    //    _dbContext.Cameras.Remove(camera);
    //    await _dbContext.SaveChangesAsync(cancellationToken);

    //    return true;
    //}
}