using Microsoft.EntityFrameworkCore;
using MineOps.Api.Models;

namespace MineOps.Api.Data;

public class MineOpsDbContext : DbContext
{
    public MineOpsDbContext(
        DbContextOptions<MineOpsDbContext> options)
        : base(options)
    {
    }

    public DbSet<Camera> Cameras => Set<Camera>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        base.OnModelCreating(modelBuilder);

        modelBuilder.ApplyConfigurationsFromAssembly(
            typeof(MineOpsDbContext).Assembly
        );
    }
}