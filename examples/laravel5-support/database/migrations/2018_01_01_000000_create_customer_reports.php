<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

class CreateCustomerReports extends Migration
{
    public function up()
    {
        Schema::create('customer_reports', function (Blueprint $table) {
            $table->increments('id');
            $table->unsignedInteger('customer_id');
            $table->string('report_type');
            $table->text('content');
            $table->string('status');
            $table->timestamps();
        });
    }
}
