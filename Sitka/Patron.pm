#!/usr/bin/perl
package Sitka::Patron;
use Sitka::DB;

sub new {
  my $class = shift;
  my $barcode = shift;
  my $ou = shift;
  my $self = {};
  bless $self, $class;
  bless $self;
  $self->{barcode}     = $barcode;
  $self->{ou}          = $ou;
  $self->{usrid}       = 0;
  $self->{givenname}   = undef;
  $self->{familyname}  = undef;
  $self->{circs}       = 0;
  $self->{holds}       = 0;
  $self->{fines}       = 0;
  $self->{msgs}        = ();
  return $self;
}

# get patron data from DB
sub retrieve {
  my $self = shift;
  my $q = Sitka::DB->connect;
  # TODO: use open-ils.actor.user.retrieve OpenSRF call instead of direct DB query 
  # (requires an OpenSRF login_session, so need to make this app's auth process use OpenSRF first)
  my $sql = 'SELECT u.id AS usr, u.first_given_name, u.family_name FROM actor.usr u
    JOIN actor.card c ON c.usr = u.id WHERE c.barcode = ? AND u.deleted IS FALSE;';
  my $result = $q->lookup($sql, $self->barcode);
  if ($result) {
    $self->usrid($result->{usr});
    $self->givenname($result->{first_given_name});
    $self->familyname($result->{family_name});
    return $self;
  } else {
    $self->msgs('FAIL_NOT_FOUND');
    return;
  }
}

sub staff_can_delete {
  my $self = shift;
  my $staffid = shift;
  my $ou = shift;
  my $q = Sitka::DB->connect;
  my $result = $q->lookup("SELECT permission.usr_has_perm(?,?,?);", $staffid, 'DELETE_USER', $ou); # query returns 't' or 'f'
  return $result->{usr_has_perm};
}

# check for active circs and holds
sub check_activity {
  my $self = shift;
  my $q = Sitka::DB->connect;
  my %checks = (
    'circs' => "SELECT count(*) AS count FROM action.circulation WHERE usr = ? AND xact_finish IS NULL;",
    'holds' => "SELECT count(*) AS count FROM action.hold_request WHERE usr = ? AND cancel_time IS NULL AND fulfillment_time IS NULL AND checkin_time IS NULL;",
  );
  foreach my $check (keys (%checks)) {
    my $sql = $checks{$check};
    my $result = $q->lookup($sql, $self->usrid);
    my $check_count = $result->{count};
    if ($check_count > 0) {
      $self->{$check} = $check_count;
      $self->msgs('FAIL_ACTIVE_XACTS') unless ( grep {'FAIL_ACTIVE_XACTS' eq $_} $self->{msgs} );
    }
  }
}

sub check_fines {
  my $self = shift;
  my $q = Sitka::DB->connect;
  my $result = $q->lookup("SELECT balance_owed FROM money.usr_summary WHERE usr = ? AND balance_owed > 0;", $self->{usrid});
  my $fines = $result->{balance_owed};
  if ($fines > 0) {
    $self->{fines} = $fines;
    $self->msgs('FAIL_HAS_FINES');
  }
}

# delete a patron and the card with the given barcode
# (other cards belonging to this user will not be affected)
sub delete_patron {
  my $self = shift;
  my $q = Sitka::DB->connect;
  # the following returns the number of rows affected, or undef if no rows were affected
  my $usr_rows_updated = $q->do( q{
      UPDATE actor.usr SET deleted = 't', active = 'f' FROM actor.card c 
      WHERE c.usr = actor.usr.id AND actor.usr.id = ? AND c.barcode = ?
    }, $self->usrid, $self->barcode );
  $q->commit;
  $self->msgs('USER_NOT_DELETED') unless ($usr_rows_updated);
  my $card_rows_deleted = $self->delete_card;
  return $usr_rows_updated;
}

sub delete_card {
  my $self = shift;
  my $q = Sitka::DB->connect;
  # the following returns the number of rows affected, or undef if no rows were affected
  my $card_rows_deleted = $q->do( q{
      DELETE FROM actor.card WHERE usr = ? AND barcode = ?;
    }, $self->usrid, $self->barcode );
  $q->commit;
  $self->msgs('CARD_NOT_DELETED') unless ($card_rows_deleted);
  return $card_rows_deleted;
}

sub barcode {
  my $self = shift;
  if (@_) { $self->{barcode} = shift; }
  return $self->{barcode};
}

sub ou {
  my $self = shift;
  if (@_) { $self->{ou} = shift; }
  return $self->{ou};
}

sub usrid {
  my $self = shift;
  if (@_) { $self->{usrid} = shift; }
  return $self->{usrid};
}

sub givenname {
  my $self = shift;
  if (@_) { $self->{givenname} = shift; }
  return $self->{givenname};
}

sub familyname {
  my $self = shift;
  if (@_) { $self->{familyname} = shift; }
  return $self->{familyname};
}

sub circs {
  my $self = shift;
  if (@_) { $self->{circs} = shift; }
  return $self->{circs};
}

sub holds {
  my $self = shift;
  if (@_) { $self->{holds} = shift; }
  return $self->{holds};
}

sub fines {
  my $self = shift;
  if (@_) { $self->{fines} = shift; }
  return $self->{fines};
}

sub msgs {
  my $self = shift;
  if (@_) { push @{$self->{msgs}}, @_; }
  return $self->{msgs};
}

1; # perl is stupid.
