<?php

namespace App\Repositories;

use App\Models\CustomerReport;
use App\Models\ReportHistory;
use Illuminate\Support\Facades\DB;

class ReportRepository
{
    public function insert(array $payload)
    {
        return CustomerReport::create($payload);
    }

    public function addHistory($reportId, $action)
    {
        return ReportHistory::create([
            'customer_report_id' => $reportId,
            'action' => $action,
        ]);
    }

    public function find($id)
    {
        return DB::table('customer_reports')
            ->whereRaw('id = ?', [$id])
            ->first();
    }
}
