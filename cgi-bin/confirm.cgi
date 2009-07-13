#!/usr/bin/perl
# confirm.cgi - retrieve patron info, check for activity, and confirm that we want to delete 'em
#
# TODO:
#   - generate HTML output
#   - construct webform so user can confirm patron deletions
use lib '..';
use lib '/openils/lib/perl5';
use CGI qw/:standard/;
#use Sitka::Patron;
use OpenSRF::System;
use OpenILS::Application::AppUtils;
use Data::Dumper;

$q = new CGI;

print header,
			start_html('Looking Up Patron'),
			h1('Looking Up...');

OpenSRF::System->bootstrap_client( config_file => '/openils/conf/opensrf_core.xml');
my $apputils = OpenILS::Application::AppUtils;

# Message codes:
# OK                 => Patron can be deleted.
# FAIL_NOT_FOUND     => Patron does not exist or does not belong to this library.
# FAIL_ACTIVE_XACTS  => Patron has active circulations or holds.
# FAIL_HAS_FINES     => Patron owes more than $0 in fines.

$ou = 0; # set this to authenticated user's OU? or more complex for multibranch?

if (param()) {
  fail('No org unit specified.') unless ($ou);
  my @input = split(/\n/, param('barcodes'));
  my (@patrons, @not_found);
  my @barcodes = clean_and_validate(@input);
  while (@barcodes) {
    my $barcode = shift @barcodes;
    my $patron = Sitka::Patron->new($barcode);
    if ($patron->retrieve()) {
      $patron->check_activity();
      $patron->check_fines();
      push @patrons, $patron;
    } else {
      push @not_found, $patron;
    }
  }
}

# TODO: form to confirm deletions (action="delete.cgi") based on results of the above checks

print end_html;

sub clean_and_validate {
  my @input = @_;
  my @output;
  while (@input) {
    my $barcode = shift @input;
    # TODO: clean up and validate barcodes
    push (@output, $barcode);
  }
  # TODO: remove duplicates from output
  return @output;
}

sub fail {
  my $msg = shift;
  print $msg;
  exit;
}

