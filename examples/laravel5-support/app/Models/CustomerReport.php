<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class CustomerReport extends Model
{
    protected $table = 'customer_reports';
    protected $fillable = ['customer_id', 'report_type', 'content', 'status'];

    public function histories()
    {
        return $this->hasMany(ReportHistory::class);
    }
}
